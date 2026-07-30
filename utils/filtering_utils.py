from __future__ import annotations

import csv
import random
import shutil
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
from PIL import Image

from utils.templates_split import (
    ClinicalCondition,
    DetectorType,
    DISEASE_COLUMNS,
    SplitNames,
    SplitType,
    View,
    BinaryClassDatasetSplitStatistic,
    BinaryClassDatasetReadError
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
    patient_images: dict[int, list[str]],
    split_names: Sequence[SplitNames],
    patient_quotas: Sequence[int],
    target_image_counts: Sequence[float],
    random_state: int,
    number_of_trials: int = 100,
) -> dict[SplitNames, list[int]]:
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

    best_partition: dict[SplitNames, list[int]] | None = None
    best_score = float("inf")

    for trial in range(number_of_trials):
        rng = random.Random(random_state + trial)

        ordered_patients = sorted(
            patients,
            key=lambda patient_id: (
                image_weights[patient_id],
                rng.random(),
            ),
            reverse=True,
        )

        partition: dict[SplitNames, list[int]] = {
            split_name: []
            for split_name in split_names
        }

        current_image_counts: dict[SplitNames, int] = {
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
    patient_images: dict[int, list[str]],
    random_state: int,
) -> dict[SplitNames, list[int]]:
    """
    Split one dictionary independently into 60%, 20%, and 20%
    patient-level subsets while balancing image counts.
    """
    split_names = tuple(SplitNames)
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
    dictionary_a: dict[int, list[str]],
    dictionary_b: dict[int, list[str]],
    random_state: int,
) -> tuple[
    dict[SplitNames, list[int]],
    dict[SplitNames, list[int]],
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

    common_training_image_target = min(
        0.60 * total_images_a,
        0.60 * total_images_b,
    )

    def split_one_dictionary(
        patient_images: dict[int, list[str]],
        seed: int,
    ) -> dict[SplitNames, list[int]]:
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
            split_names=tuple(SplitNames),
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
    db_path: str | Path,
    kvp: float,
    detector_type: DetectorType,
    mas_range: Sequence[float],
    clinical_condition: ClinicalCondition,
    view: View,
) -> dict[int, list[str]]:
    """
    Filter images stored in a SQLite database.

    For a particular finding, the corresponding label must equal 1.

    For ClinicalCondition.HEALTHY, every disease label in
    DISEASE_COLUMNS must explicitly equal 0. Values of -1 or NULL
    are therefore excluded.
    """
    db_path = Path(db_path)

    if not db_path.is_file():
        raise FileNotFoundError(
            f"SQLite database was not found: {db_path}"
        )

    # Runtime validation is retained even though the parameters are typed.
    # This also produces a clear error if a raw invalid string is passed.
    try:
        detector_type = DetectorType(detector_type)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in DetectorType)
        raise ValueError(
            f"Unknown detector type: {detector_type!r}. "
            f"Allowed values are: {allowed}."
        ) from exc

    try:
        clinical_condition = ClinicalCondition(clinical_condition)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ClinicalCondition)
        raise ValueError(
            f"Unknown clinical condition: {clinical_condition!r}. "
            f"Allowed values are: {allowed}."
        ) from exc

    try:
        view = View(view)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in View)
        raise ValueError(
            f"Unknown view: {view!r}. Allowed values are: {allowed}."
        ) from exc

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

    if clinical_condition is ClinicalCondition.HEALTHY:
        clinical_filter = " AND ".join(
            f"cd.{column} = 0"
            for column in DISEASE_COLUMNS
        )
    else:
        # The column name comes from ClinicalCondition, not arbitrary input.
        clinical_filter = (
            f"cd.{clinical_condition.value} = 1"
        )

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

    parameters: tuple[float, str, float, float, str] = (
        float(kvp),
        detector_type.value,
        min_mas,
        max_mas,
        view.value,
    )

    images_by_patient: defaultdict[int, list[str]] = defaultdict(list)

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(query, parameters)

        for subject_id, file_path in cursor:
            images_by_patient[int(subject_id)].append(str(file_path))

    return dict(images_by_patient)


def filter_patients(
    images_dict_1: dict[int, list[str]],
    images_dict_2: dict[int, list[str]],
) -> list[int]:
    """
    Return patient IDs present in both dictionaries.
    """
    intersecting_pids = images_dict_1.keys() & images_dict_2.keys()
    return list(intersecting_pids)


def clear_patients(
    images_dict_1: dict[int, list[str]],
    images_dict_2: dict[int, list[str]],
    pids: list[int],
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
    split_type: SplitType,
    output_path: str | Path,
    image_converting_function: Callable[[str | Path], np.ndarray] | None = None,
    random_state: int = 42,
) -> tuple[
    dict[BinaryClassDatasetSplitStatistic, int],
    dict[BinaryClassDatasetReadError, list[str]],
]:
    """
    Split two image dictionaries and generate image and CSV datasets.

    dictionary_a represents the negative class, label 0.
    dictionary_b represents the positive class, label 1.

    Patient statistics contain the number of patients assigned to each
    split. Image statistics contain only successfully saved images.

    Images that cannot be read, converted, copied, or saved are skipped
    and added to error_report.

    Returns
    -------
    tuple
        (
            split_report,
            error_report,
        )
    """
    try:
        split_type = SplitType(split_type)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in SplitType)
        raise ValueError(
            f"Unknown split type: {split_type!r}. "
            f"Allowed values are: {allowed}."
        ) from exc

    overlapping_patients = set(dictionary_a) & set(dictionary_b)

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

    split_names = tuple(SplitNames)

    for split_name in split_names:
        (images_root / split_name.value).mkdir(
            parents=True,
            exist_ok=True,
        )

    csv_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    if split_type is SplitType.BALANCED:
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

    # Maps a split and class label to the corresponding patient statistic.
    patient_statistic_keys: dict[
        tuple[SplitNames, int],
        BinaryClassDatasetSplitStatistic,
    ] = {
        (
            SplitNames.TRAINING,
            1,
        ): BinaryClassDatasetSplitStatistic.TRAIN_POSITIVE_PATIENT_NUM,
        (
            SplitNames.TRAINING,
            0,
        ): BinaryClassDatasetSplitStatistic.TRAIN_NEGATIVE_PATIENT_NUM,
        (
            SplitNames.VALIDATION,
            1,
        ): BinaryClassDatasetSplitStatistic.VALIDATION_POSITIVE_PATIENT_NUM,
        (
            SplitNames.VALIDATION,
            0,
        ): BinaryClassDatasetSplitStatistic.VALIDATION_NEGATIVE_PATIENT_NUM,
        (
            SplitNames.TEST,
            1,
        ): BinaryClassDatasetSplitStatistic.TEST_POSITIVE_PATIENT_NUM,
        (
            SplitNames.TEST,
            0,
        ): BinaryClassDatasetSplitStatistic.TEST_NEGATIVE_PATIENT_NUM,
    }

    # Maps a split and class label to the corresponding image statistic.
    image_statistic_keys: dict[
        tuple[SplitNames, int],
        BinaryClassDatasetSplitStatistic,
    ] = {
        (
            SplitNames.TRAINING,
            1,
        ): BinaryClassDatasetSplitStatistic.TRAIN_POSITIVE_IMAGE_NUM,
        (
            SplitNames.TRAINING,
            0,
        ): BinaryClassDatasetSplitStatistic.TRAIN_NEGATIVE_IMAGE_NUM,
        (
            SplitNames.VALIDATION,
            1,
        ): BinaryClassDatasetSplitStatistic.VALIDATION_POSITIVE_IMAGE_NUM,
        (
            SplitNames.VALIDATION,
            0,
        ): BinaryClassDatasetSplitStatistic.VALIDATION_NEGATIVE_IMAGE_NUM,
        (
            SplitNames.TEST,
            1,
        ): BinaryClassDatasetSplitStatistic.TEST_POSITIVE_IMAGE_NUM,
        (
            SplitNames.TEST,
            0,
        ): BinaryClassDatasetSplitStatistic.TEST_NEGATIVE_IMAGE_NUM,
    }

    # Maps a split and class label to the corresponding error category.
    error_report_keys: dict[
        tuple[SplitNames, int],
        BinaryClassDatasetReadError,
    ] = {
        (
            SplitNames.TRAINING,
            1,
        ): BinaryClassDatasetReadError.TRAIN_POSITIVE,
        (
            SplitNames.TRAINING,
            0,
        ): BinaryClassDatasetReadError.TRAIN_NEGATIVE,
        (
            SplitNames.VALIDATION,
            1,
        ): BinaryClassDatasetReadError.VALIDATION_POSITIVE,
        (
            SplitNames.VALIDATION,
            0,
        ): BinaryClassDatasetReadError.VALIDATION_NEGATIVE,
        (
            SplitNames.TEST,
            1,
        ): BinaryClassDatasetReadError.TEST_POSITIVE,
        (
            SplitNames.TEST,
            0,
        ): BinaryClassDatasetReadError.TEST_NEGATIVE,
    }

    # Initialize every statistic with zero.
    split_report: dict[
        BinaryClassDatasetSplitStatistic,
        int,
    ] = {
        statistic: 0
        for statistic in BinaryClassDatasetSplitStatistic
    }

    # Initialize every error category with an empty list.
    error_report: dict[
        BinaryClassDatasetReadError,
        list[str],
    ] = {
        error_type: []
        for error_type in BinaryClassDatasetReadError
    }

    # Patient counts are based on patients assigned to each split,
    # independently of whether individual images can be processed.
    for label, patient_splits in (
        (0, splits_a),
        (1, splits_b),
    ):
        for split_name in split_names:
            statistic_key = patient_statistic_keys[
                split_name,
                label,
            ]

            split_report[statistic_key] = len(
                patient_splits[split_name]
            )

    csv_rows: dict[
        SplitNames,
        list[dict[str, str | int]],
    ] = {
        split_name: []
        for split_name in split_names
    }

    for label, patient_dictionary, patient_splits in (
        (0, dictionary_a, splits_a),
        (1, dictionary_b, splits_b),
    ):
        for split_name in split_names:
            destination_folder = (
                images_root / split_name.value
            )

            image_statistic_key = image_statistic_keys[
                split_name,
                label,
            ]

            error_report_key = error_report_keys[
                split_name,
                label,
            ]

            for patient_id in patient_splits[split_name]:
                source_paths = patient_dictionary[patient_id]

                for source_path_value in source_paths:
                    source_path = Path(source_path_value)
                    destination_path: Path | None = None

                    try:
                        if not source_path.is_file():
                            raise FileNotFoundError(
                                f"Image was not found: {source_path}"
                            )

                        pid = source_path.parent.parent.name
                        sid = source_path.parent.name
                        iid = source_path.stem

                        if image_converting_function is None:
                            destination_path = (
                                destination_folder
                                / f"{pid}_{sid}_{source_path.name}"
                            )

                            shutil.copy2(
                                source_path,
                                destination_path,
                            )
                        else:
                            destination_path = (
                                destination_folder
                                / f"{pid}_{sid}_{iid}.png"
                            )

                            image_array = image_converting_function(
                                source_path
                            )

                            image_array = _prepare_array_for_png(
                                image_array
                            )

                            Image.fromarray(image_array).save(
                                destination_path
                            )

                    except Exception as error:
                        # Remove a partially created output file, if any.
                        if (
                            destination_path is not None
                            and destination_path.exists()
                        ):
                            destination_path.unlink()

                        error_report[error_report_key].append(
                            str(source_path)
                        )

                        print(
                            f"Failed image: {source_path}. "
                            f"Error: {error}"
                        )

                        continue

                    # This point is reached only after successful
                    # copying or PNG generation.
                    split_report[image_statistic_key] += 1

                    csv_rows[split_name].append(
                        {
                            "filename": str(
                                destination_path.resolve()
                            ),
                            "label": label,
                        }
                    )

    for split_name in split_names:
        csv_path = csv_root / f"{split_name.value}.csv"

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

    return split_report, error_report