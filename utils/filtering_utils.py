from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Callable, Hashable, Mapping, Dict, List, Sequence, Tuple, Union


import csv
import random
import shutil

import numpy as np
from PIL import Image


PatientID = Hashable
PatientImages = Mapping[PatientID, Sequence[str | Path]]
ConvertingFunction = Callable[[str | Path], np.ndarray]



CLINICAL_CONDITIONS = {
    "atelectasis",
    "cardiomegaly",
    "consolidation",
    "edema",
    "enlarged_cardiomediastinum",
    "fracture",
    "lung_lesion",
    "lung_opacity",
    "no_finding",
    "pleural_effusion",
    "pleural_other",
    "pneumonia",
    "pneumothorax",
    "healthy",
}

# Labels that represent actual findings.
# no_finding is handled separately and is not treated as a disease.
DISEASE_COLUMNS = (
    "atelectasis",
    "cardiomegaly",
    "consolidation",
    "edema",
    "enlarged_cardiomediastinum",
    "fracture",
    "lung_lesion",
    "lung_opacity",
    "pleural_effusion",
    "pleural_other",
    "pneumonia",
    "pneumothorax",
)



def _calculate_split_counts(
    number_of_patients: int,
    fractions: Sequence[float],
) -> list[int]:
    """
    Convert fractional split sizes into integer patient counts.

    The returned counts always sum to number_of_patients.
    """
    raw_counts = [number_of_patients * fraction for fraction in fractions]
    counts = [int(value) for value in raw_counts]

    remaining = number_of_patients - sum(counts)

    fractional_parts = [
        raw - integer
        for raw, integer in zip(raw_counts, counts)
    ]

    order = sorted(
        range(len(fractions)),
        key=lambda index: fractional_parts[index],
        reverse=True,
    )

    for index in order[:remaining]:
        counts[index] += 1

    return counts


def _weighted_patient_partition(
    patient_images: PatientImages,
    split_names: Sequence[str],
    patient_quotas: Sequence[int],
    target_image_counts: Sequence[float],
    random_state: int,
    number_of_trials: int = 100,
) -> dict[str, list[PatientID]]:
    """
    Assign patients to splits while respecting patient quotas and
    approximately matching target image counts.
    """
    if len(split_names) != len(patient_quotas):
        raise ValueError(
            "split_names and patient_quotas must have the same length."
        )

    if len(split_names) != len(target_image_counts):
        raise ValueError(
            "split_names and target_image_counts must have the same length."
        )

    if sum(patient_quotas) != len(patient_images):
        raise ValueError(
            "The patient quotas must sum to the number of patients."
        )

    patients = list(patient_images.keys())

    image_weights = {
        patient_id: len(patient_images[patient_id])
        for patient_id in patients
    }

    best_partition: dict[str, list[PatientID]] | None = None
    best_score = float("inf")

    for trial in range(number_of_trials):
        rng = random.Random(random_state + trial)

        # Large patients are assigned first. A small random component
        # allows repeated trials to explore different valid partitions.
        ordered_patients = sorted(
            patients,
            key=lambda patient_id: (
                image_weights[patient_id],
                rng.random(),
            ),
            reverse=True,
        )

        partition = {
            split_name: []
            for split_name in split_names
        }

        current_image_counts = {
            split_name: 0
            for split_name in split_names
        }

        for patient_id in ordered_patients:
            patient_weight = image_weights[patient_id]

            available_splits = [
                index
                for index, split_name in enumerate(split_names)
                if len(partition[split_name]) < patient_quotas[index]
            ]

            best_split_index = min(
                available_splits,
                key=lambda index: (
                    abs(
                        current_image_counts[split_names[index]]
                        + patient_weight
                        - target_image_counts[index]
                    )
                    / max(target_image_counts[index], 1.0),
                    rng.random(),
                ),
            )

            selected_split = split_names[best_split_index]

            partition[selected_split].append(patient_id)
            current_image_counts[selected_split] += patient_weight

        score = sum(
            abs(
                current_image_counts[split_name]
                - target_image_counts[index]
            )
            / max(target_image_counts[index], 1.0)
            for index, split_name in enumerate(split_names)
        )

        if score < best_score:
            best_score = score
            best_partition = partition

    if best_partition is None:
        raise RuntimeError("Patient partitioning failed.")

    return best_partition


def _split_60_20_20(
    patient_images: PatientImages,
    random_state: int,
) -> dict[str, list[PatientID]]:
    """
    Split one dictionary independently into 60%, 20%, and 20%
    patient-level subsets while balancing image counts.
    """
    split_names = ("training", "validation", "test")
    fractions = (0.60, 0.20, 0.20)

    patient_quotas = _calculate_split_counts(
        len(patient_images),
        fractions,
    )

    total_images = sum(
        len(image_paths)
        for image_paths in patient_images.values()
    )

    target_image_counts = [
        total_images * fraction
        for fraction in fractions
    ]

    return _weighted_patient_partition(
        patient_images=patient_images,
        split_names=split_names,
        patient_quotas=patient_quotas,
        target_image_counts=target_image_counts,
        random_state=random_state,
    )


def _split_balanced_training(
    dictionary_a: PatientImages,
    dictionary_b: PatientImages,
    random_state: int,
) -> tuple[
    dict[str, list[PatientID]],
    dict[str, list[PatientID]],
]:
    """
    Create balanced training sets.

    Both training sets contain 60% of the patient count from the
    smaller dictionary. The selected subsets are also chosen to make
    the image counts as similar as possible.

    Remaining patients from each dictionary are divided equally
    between validation and test.
    """
    smaller_patient_count = min(
        len(dictionary_a),
        len(dictionary_b),
    )

    training_patient_count = round(
        0.60 * smaller_patient_count
    )

    total_images_a = sum(
        len(paths)
        for paths in dictionary_a.values()
    )
    total_images_b = sum(
        len(paths)
        for paths in dictionary_b.values()
    )

    # Common image target for both training classes.
    common_training_image_target = min(
        0.60 * total_images_a,
        0.60 * total_images_b,
    )

    def split_one_dictionary(
        patient_images: PatientImages,
        seed: int,
    ) -> dict[str, list[PatientID]]:
        remaining_patient_count = (
            len(patient_images) - training_patient_count
        )

        validation_count, test_count = _calculate_split_counts(
            remaining_patient_count,
            (0.50, 0.50),
        )

        total_images = sum(
            len(paths)
            for paths in patient_images.values()
        )

        remaining_image_target = max(
            total_images - common_training_image_target,
            0,
        )

        return _weighted_patient_partition(
            patient_images=patient_images,
            split_names=("training", "validation", "test"),
            patient_quotas=(
                training_patient_count,
                validation_count,
                test_count,
            ),
            target_image_counts=(
                common_training_image_target,
                remaining_image_target / 2,
                remaining_image_target / 2,
            ),
            random_state=seed,
        )

    split_a = split_one_dictionary(
        dictionary_a,
        random_state,
    )

    split_b = split_one_dictionary(
        dictionary_b,
        random_state + 10_000,
    )

    return split_a, split_b


def _prepare_array_for_png(image_array: np.ndarray) -> np.ndarray:
    """
    Convert an image array into a PNG-compatible NumPy array.
    """
    array = np.asarray(image_array)
    array = np.squeeze(array)

    if array.ndim not in (2, 3):
        raise ValueError(
            "The converting function must return a 2D grayscale image "
            "or a 3D color image."
        )

    if np.issubdtype(array.dtype, np.floating):
        finite_mask = np.isfinite(array)

        if not finite_mask.any():
            raise ValueError(
                "The converted image contains no finite values."
            )

        minimum = array[finite_mask].min()
        maximum = array[finite_mask].max()

        if maximum > minimum:
            array = (
                (array - minimum)
                / (maximum - minimum)
                * 255
            )
        else:
            array = np.zeros_like(array)

        array = np.nan_to_num(
            array,
            nan=0,
            posinf=255,
            neginf=0,
        ).astype(np.uint8)

    elif array.dtype == np.bool_:
        array = array.astype(np.uint8) * 255

    elif np.issubdtype(array.dtype, np.integer):
        minimum = array.min()
        maximum = array.max()

        if minimum >= 0 and maximum <= 255:
            array = array.astype(np.uint8)
        elif minimum >= 0 and maximum <= 65535:
            array = array.astype(np.uint16)
        else:
            if maximum > minimum:
                array = (
                    (array.astype(np.float32) - minimum)
                    / (maximum - minimum)
                    * 255
                ).astype(np.uint8)
            else:
                array = np.zeros_like(
                    array,
                    dtype=np.uint8,
                )
    else:
        raise TypeError(
            f"Unsupported image dtype: {array.dtype}"
        )

    return array





def filter_images(
    db_path: Union[str, Path],
    kvp: float,
    detector_type: str,
    mas_range: Sequence[float],
    clinical_condition: str,
    view: str,
) -> Dict[int, List[str]]:
    """
    Filter images stored in a SQLite database.

    Parameters
    ----------
    db_path
        Path to the SQLite database.

    kvp
        Required kVp value. Exact SQL equality is used.

    detector_type
        Required detector type code.

    mas_range
        Two-element sequence containing:
            (minimum_mAs, maximum_mAs)

        Both boundaries are inclusive.

    clinical_condition
        One of:
            atelectasis
            cardiomegaly
            consolidation
            edema
            enlarged_cardiomediastinum
            fracture
            lung_lesion
            lung_opacity
            no_finding
            pleural_effusion
            pleural_other
            pneumonia
            pneumothorax
            healthy

        For a particular finding, the corresponding label must equal 1.

        For "healthy", every disease label in DISEASE_COLUMNS must
        explicitly equal 0. Values of -1 or NULL are therefore excluded.

        The no_finding label is not used to define "healthy", because it is
        a separate CheXpert observation. It can be selected explicitly with
        clinical_condition="no_finding".

    view
        Required image view code.

    Returns
    -------
    dict
        Dictionary of the form:

        {
            subject_id: [file_path_1, file_path_2, ...]
        }
    """
    db_path = Path(db_path)

    if not db_path.is_file():
        raise FileNotFoundError(f"SQLite database was not found: {db_path}")

    condition = clinical_condition.strip().lower()

    if condition not in CLINICAL_CONDITIONS:
        allowed = ", ".join(sorted(CLINICAL_CONDITIONS))
        raise ValueError(
            f"Unknown clinical condition: {clinical_condition!r}. "
            f"Allowed values are: {allowed}"
        )

    if len(mas_range) != 2:
        raise ValueError(
            "mas_range must contain exactly two values: "
            "(minimum_mAs, maximum_mAs)."
        )

    min_mas, max_mas = map(float, mas_range)

    if min_mas > max_mas:
        raise ValueError(
            f"Invalid mAs range: minimum {min_mas} is greater than "
            f"maximum {max_mas}."
        )

    if condition == "healthy":
        # Strict healthy:
        # all disease labels must be explicitly equal to zero.
        clinical_filter = " AND ".join(
            f"cd.{column} = 0" for column in DISEASE_COLUMNS
        )
    else:
        # Column names cannot be passed as SQL parameters, so the condition
        # is validated against CLINICAL_CONDITIONS before being inserted.
        clinical_filter = f"cd.{condition} = 1"

    query = f"""
        SELECT
            s.subject_id,
            i.file_path
        FROM studies AS s
        INNER JOIN images AS i
            ON i.study_id = s.study_id
        INNER JOIN image_acquisition AS ia
            ON ia.image_id = i.image_id
        INNER JOIN chexpert_diagnosis AS cd
            ON cd.study_id = s.study_id
        WHERE ia.kvp = ?
          AND ia.detector_type_code = ?
          AND ia.exposure_mas BETWEEN ? AND ?
          AND ia.view_code = ?
          AND i.file_path IS NOT NULL
          AND {clinical_filter}
        ORDER BY
            s.subject_id,
            i.file_path
    """

    parameters: Tuple[float, str, float, float, str] = (
        float(kvp),
        detector_type,
        min_mas,
        max_mas,
        view,
    )

    images_by_patient: defaultdict[int, List[str]] = defaultdict(list)

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(query, parameters)

        for subject_id, file_path in cursor:
            images_by_patient[int(subject_id)].append(str(file_path))

    return dict(images_by_patient)


def filter_patients(
    images_dict_1: Dict[int, List[str]],
    images_dict_2: Dict[int, List[str]],
) -> List[int]:
    """
    Return patient IDs present in both dictionaries.
    """
    intersecting_pids = images_dict_1.keys() & images_dict_2.keys()
    return list(intersecting_pids)


def clear_patients(
    images_dict_1: Dict[int, List[str]],
    images_dict_2: Dict[int, List[str]],
    pids: List[int],
) -> None:
    """
    Delete the specified patient IDs from the dictionary containing
    the largest number of patients.

    The input dictionary is modified in place. Nothing is returned.

    If both dictionaries have the same number of keys, images_dict_1
    is selected.
    """
    if len(images_dict_1) >= len(images_dict_2):
        largest_dict = images_dict_1
    else:
        largest_dict = images_dict_2

    for pid in pids:
        largest_dict.pop(pid, None)




def split_datasets(
    dictionary_a: dict[int, list[str]],
    dictionary_b: dict[int, list[str]],
    split_type: str,
    output_path: str | Path,
    image_converting_function: Callable[[str | Path], np.ndarray] | None = None,
    random_state: int = 42,
) -> None:
    """
    Split two image dictionaries and generate image and CSV datasets.

    Parameters
    ----------
    dictionary_a
        Patient dictionary for class 0:

            {
                patient_id: [dicom_path_1, dicom_path_2, ...]
            }

    dictionary_b
        Patient dictionary for class 1.

    split_type
        Either:

        - "balanced"
        - "60-20-20"

        In balanced mode, both training classes contain the same
        patient count: 60% of the smaller dictionary's patient count.
        Patient image counts are used as weights to minimize class
        imbalance in terms of images.

        In 60-20-20 mode, each dictionary is split independently.

    output_path
        Root directory where the generated dataset is written.

    image_converting_function
        Optional function with this interface:

            image_array = image_converting_function(dicom_path)

        The returned NumPy array is saved as PNG.

        When no function is provided, source files are copied unchanged.
        Therefore, copied DICOM files remain DICOM files.

    random_state
        Seed used for reproducible patient-level splitting.

    Returns
    -------
    None
        Files and CSV tables are written to disk.
    """
    normalized_split_type = split_type.strip().lower()

    if normalized_split_type not in {
        "balanced",
        "60-20-20",
    }:
        raise ValueError(
            "split_type must be either 'balanced' or '60-20-20'."
        )

    overlapping_patients = (
        set(dictionary_a.keys())
        & set(dictionary_b.keys())
    )

    if overlapping_patients:
        raise ValueError(
            f"The two dictionaries contain "
            f"{len(overlapping_patients)} overlapping patient IDs. "
            "Remove overlapping patients before splitting."
        )

    if not dictionary_a:
        raise ValueError("dictionary_a is empty.")

    if not dictionary_b:
        raise ValueError("dictionary_b is empty.")

    output_path = Path(output_path)

    images_root = output_path / "images"
    csv_root = output_path / "csv"

    split_names = ("training", "validation", "test")

    for split_name in split_names:
        (images_root / split_name).mkdir(
            parents=True,
            exist_ok=True,
        )

    csv_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    if normalized_split_type == "balanced":
        splits_a, splits_b = _split_balanced_training(
            dictionary_a=dictionary_a,
            dictionary_b=dictionary_b,
            random_state=random_state,
        )
    else:
        splits_a = _split_60_20_20(
            patient_images=dictionary_a,
            random_state=random_state,
        )

        splits_b = _split_60_20_20(
            patient_images=dictionary_b,
            random_state=random_state + 10_000,
        )

    csv_rows = {
        split_name: []
        for split_name in split_names
    }

    for label, patient_dictionary, patient_splits in (
        (0, dictionary_a, splits_a),
        (1, dictionary_b, splits_b),
    ):
        for split_name in split_names:
            destination_folder = images_root / split_name

            for patient_id in patient_splits[split_name]:
                source_paths = patient_dictionary[patient_id]

                for image_index, source_path in enumerate(source_paths):
                    source_path = Path(source_path)

                    if not source_path.is_file():
                        raise FileNotFoundError(
                            f"Image was not found: {source_path}"
                        )

                    if image_converting_function is None:
                        destination_path = (
                            destination_folder / source_path.name
                        )

                        shutil.copy2(
                            source_path,
                            destination_path,
                        )
                    else:
                        destination_name = (
                            f"{source_path.stem}.png"
                        )

                        destination_path = (
                            destination_folder / destination_name
                        )
                        try:
                            image_array = image_converting_function(
                                source_path
                            )
                        except Exception as error:
                            print(f"Failed image: {source_path}")
                            raise

                        image_array = _prepare_array_for_png(
                            image_array
                        )

                        Image.fromarray(image_array).save(
                            destination_path
                        )

                    csv_rows[split_name].append(
                        {
                            "filename": str(
                                destination_path.resolve()
                            ),
                            "label": label,
                        }
                    )

    for split_name in split_names:
        csv_path = csv_root / f"{split_name}.csv"

        with csv_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["filename", "label"],
            )

            writer.writeheader()
            writer.writerows(csv_rows[split_name])


