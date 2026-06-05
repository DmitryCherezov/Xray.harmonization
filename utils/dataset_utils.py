import sqlite3
import pydicom
import pandas as pd
from typing import Any
from pathlib import Path
from types import ModuleType
from dataclasses import fields
from typing import List, TextIO
from pydicom.dataset import FileDataset
from config.settings_data import CSVSettings



def check_MIMIC_IV_csv_file_existance(
        csv_settings: CSVSettings,
        T: ModuleType
    ):

    report = {
        'files_checked':0,
        'exist':[],
        'missing':[]
    }

    for f in fields(csv_settings):
        name = f.name
        file_path = getattr(csv_settings, name)
        report['files_checked'] += 1
        if file_path.exists():
            report['exist'].append(file_path)
        else:
            report['missing'].append(file_path)
    
    print(
        T.MESSAGE_NUMBER_CSV_FILES_CHECKED.format(
            csv_file_num=report['files_checked']
        )
    )
    for missing_path in report['missing']:
        print(
            T.MESSAGE_REQUIRED_CSV_NOT_FOUND.format(
                csv_file_path=missing_path
            )
        )
    
    return report



def write_to_file(fid: TextIO, line: str) -> None:
    fid.write(line)
    fid.flush()

def _get_dicom_value(ds: FileDataset, keyword: str) -> Any:
    value = getattr(ds, keyword, None)

    if value is None:
        return None

    # pydicom types: DSfloat, IS, MultiValue, PersonName, etc.
    # Для записи в CSV/SQLite лучше привести к обычным Python-типам.
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]

    return value


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> str | None:
    if value is None:
        return None

    return str(value)


def get_acquisition_parameters(
    file_path: Path,
    DICOM_tags: dict[str, str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    ds = pydicom.dcmread(
        file_path,
        stop_before_pixels=True,
        force=True,
    )

    # Простые поля
    result["view_code"] = _to_str(_get_dicom_value(ds, DICOM_tags["view_code"]))
    result["kvp"] = _to_float(_get_dicom_value(ds, DICOM_tags["kvp"]))
    result["detector_type_code"] = _to_str(
        _get_dicom_value(ds, DICOM_tags["detector_type_code"])
    )

    result["rows"] = _to_int(_get_dicom_value(ds, DICOM_tags["rows"]))
    result["cols"] = _to_int(_get_dicom_value(ds, DICOM_tags["cols"]))

    result["exposure_mas"] = _to_float(
        _get_dicom_value(ds, DICOM_tags["exposure_mas"])
    )
    result["exposure_time_ms"] = _to_float(
        _get_dicom_value(ds, DICOM_tags["exposure_time_ms"])
    )

    result["body_part"] = _to_str(_get_dicom_value(ds, DICOM_tags["body_part"]))
    result["manufacturer"] = _to_str(
        _get_dicom_value(ds, DICOM_tags["manufacturer"])
    )
    result["model_name"] = _to_str(
        _get_dicom_value(ds, DICOM_tags["model_name"])
    )

    # PixelSpacing: [row_spacing, col_spacing]
    pixel_spacing = _get_dicom_value(ds, DICOM_tags["pixel_spacing"])

    result["pixel_spacing_row"] = None
    result["pixel_spacing_col"] = None

    if pixel_spacing is not None and len(pixel_spacing) >= 2:
        result["pixel_spacing_row"] = _to_float(pixel_spacing[0])
        result["pixel_spacing_col"] = _to_float(pixel_spacing[1])

    return result


def generate_image_acquisition_parameter_csv(
    data_path: Path,
    images_path: Path,
    acquisition_path: Path,
    image_extensions: list[str] | None = None,
    ) -> None:
    
    if image_extensions is None:
        image_extensions = [".dcm"]

    image_extensions = [ext.lower() for ext in image_extensions]

    images_header = "image_id,study_id,file_path\n"

    acquisition_columns = [
        "view_code",
        "kvp",
        "detector_type_code",
        "rows",
        "cols",
        "pixel_spacing_row",
        "pixel_spacing_col",
        "exposure_mas",
        "exposure_time_ms",
        "body_part",
        "manufacturer",
        "model_name",
    ]

    acquisition_header = "image_id," + ",".join(acquisition_columns) + "\n"

    DICOM_TAGS = {
        "view_code": "ViewPosition",
        "kvp": "KVP",
        "detector_type_code": "DetectorType",
        "rows": "Rows",
        "cols": "Columns",
        "pixel_spacing": "PixelSpacing",
        "exposure_mas": "Exposure",
        "exposure_time_ms": "ExposureTime",
        "body_part": "BodyPartExamined",
        "manufacturer": "Manufacturer",
        "model_name": "ManufacturerModelName",
    }

    with open(images_path, "w", encoding="utf-8") as image_fid:
        with open(acquisition_path, "w", encoding="utf-8") as acquisition_fid:
            write_to_file(image_fid, images_header)
            write_to_file(acquisition_fid, acquisition_header)

            for file_path in data_path.rglob("*"):
                if not file_path.is_file():
                    continue

                if file_path.suffix.lower() not in image_extensions:
                    continue

                image_id = file_path.stem

                study_id = file_path.parent.name
                subject_id = file_path.parent.parent.name

                if study_id.startswith("s"):
                    study_id = study_id[1:]

                if subject_id.startswith("p"):
                    subject_id = subject_id[1:]

                images_table_row = f"{image_id},{study_id},{file_path}\n"

                acquisition_table_values = get_acquisition_parameters(
                    file_path=file_path,
                    DICOM_tags=DICOM_TAGS,
                )

                acquisition_values = [
                    str(acquisition_table_values.get(column, ""))
                    for column in acquisition_columns
                ]

                acquisition_table_values_row = (
                    image_id + "," + ",".join(acquisition_values) + "\n"
                )

                write_to_file(image_fid, images_table_row)
                write_to_file(acquisition_fid, acquisition_table_values_row)


def format_mimic_chexpert_diagnostic_csv(
    source_csv_path:Path,
    target_csv_path:Path,
    drop_column: str = "subject_id",
    fill_value: int | float = 0,
) -> None:
    df = pd.read_csv(source_csv_path)

    if drop_column in df.columns:
        df = df.drop(columns=[drop_column])

    df = df.fillna(fill_value)

    target_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_csv_path, index=False)

def create_studies_csv(
    input_csv_path: Path,
    output_csv_path: Path,
    sep: str = ",",
) -> None:

    input_csv_path = Path(input_csv_path)
    output_csv_path = Path(output_csv_path)

    if not input_csv_path.exists():
        raise FileNotFoundError(f"Input CSV file not found: {input_csv_path}")

    df = pd.read_csv(input_csv_path, sep=sep)

    required_columns = {"study_id", "subject_id"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing columns in input CSV: {missing_columns}")

    # Проверяем, что один study_id не связан с несколькими subject_id
    study_subject_counts = (
        df.groupby("study_id")["subject_id"]
        .nunique()
    )

    conflict_study_ids = study_subject_counts[study_subject_counts > 1]

    if not conflict_study_ids.empty:
        conflicts = (
            df[df["study_id"].isin(conflict_study_ids.index)]
            [["study_id", "subject_id"]]
            .drop_duplicates()
            .sort_values(["study_id", "subject_id"])
        )

        raise ValueError(
            "Some study_id values are linked to multiple subject_id values:\n"
            f"{conflicts}"
        )

    studies_df = (
        df[["study_id", "subject_id"]]
        .drop_duplicates()
        .sort_values("study_id")
        .reset_index(drop=True)
    )

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    studies_df.to_csv(output_csv_path, index=False)



def create_database_from_sql(
    db_path: Path,
    schema_path: Path,
    overwrite: bool = False,
) -> None:
    if overwrite and db_path.exists():
        db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        schema_sql = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema_sql)

        conn.commit()



def get_csv_table_mapping(
        settings:CSVSettings    
):
    TABLE_INSERT_ORDER = [
    # 1. Root / dictionary tables
    "patients",
    "provider",
    "d_hcpcs",
    "d_icd_diagnoses",
    "d_icd_procedures",
    "d_labitems",

    # 2. Core hospital admissions
    "admissions",

    # 3. Tables depending on patients/admissions/dictionaries
    "omr",
    "hcpcsevents",
    "diagnoses_icd",
    "procedures_icd",
    "labevents",
    "microbiologyevents",
    "drgcodes",
    "services",
    "transfers",

    # 4. POE / medication chain
    "poe",
    "poe_detail",
    "pharmacy",
    "prescriptions",
    "emar",
    "emar_detail",

    # 5. Imaging part
    "studies",
    "images",
    "image_acquisition",
    "chexpert_diagnosis",
    ]

    TABLE_TO_CSV = {
    "patients": settings.patients_csv,
    "provider": settings.provider_csv,
    "d_hcpcs": settings.d_hcpcs_csv,
    "d_icd_diagnoses": settings.d_icd_diagnoses_csv,
    "d_icd_procedures": settings.d_icd_procedures_csv,
    "d_labitems": settings.d_labitems_csv,

    "admissions": settings.admission_csv,
    "omr": settings.omr_csv,
    "hcpcsevents": settings.hcpcsevents_csv,
    "diagnoses_icd": settings.diagnoses_icd_csv,
    "procedures_icd": settings.procedures_icd_csv,
    "labevents": settings.labevents_csv,
    "microbiologyevents": settings.microbiologyevents_csv,
    "drgcodes": settings.drgcodes_csv,
    "services": settings.services_csv,
    "transfers": settings.transfers_csv,

    "poe": settings.poe_csv,
    "poe_detail": settings.poe_detail_csv,
    "pharmacy": settings.pharmacy_csv,
    "prescriptions": settings.prescriptions_csv,
    "emar": settings.emar_csv,
    "emar_detail": settings.emar_detail_csv,

    "studies": settings.studies_csv,
    "images": settings.images_csv,
    "image_acquisition": settings.image_acquisition_csv,
    "chexpert_diagnosis": settings.formated_chexpert_diagnosis_csv,
}

    return TABLE_INSERT_ORDER, TABLE_TO_CSV

CHEXPERT_COLUMN_MAPPING = {
    "Atelectasis": "atelectasis",
    "Cardiomegaly": "cardiomegaly",
    "Consolidation": "consolidation",
    "Edema": "edema",
    "Enlarged Cardiomediastinum": "enlarged_cardiomediastinum",
    "Fracture": "fracture",
    "Lung Lesion": "lung_lesion",
    "Lung Opacity": "lung_opacity",
    "No Finding": "no_finding",
    "Pleural Effusion": "pleural_effusion",
    "Pleural Other": "pleural_other",
    "Pneumonia": "pneumonia",
    "Pneumothorax": "pneumothorax",
    "Support Devices": "support_devices",
}

def inject_csv_to_table(
    db_path: Path,
    csv_path: Path,
    table_name: str,
    chunksize: int = 100_000,
) -> None:
    """
    Reads CSV or CSV.GZ file by chunks and inserts data into an existing SQLite table.
    """

    db_path = Path(db_path)
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        for chunk in pd.read_csv(csv_path, chunksize=chunksize, low_memory=False):

            if table_name == "chexpert_diagnosis":
                chunk = chunk.rename(columns=CHEXPERT_COLUMN_MAPPING)
                
            chunk.to_sql(
                name=table_name,
                con=conn,
                if_exists="append",
                index=False,
            )

        conn.commit()

def drop_table_data(
    db_path: Path,
    table_name: str
) -> None:

    db_path = Path(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check that table exists
        #cursor.execute(
        #    """
        #    SELECT name
        #    FROM sqlite_master
        #    WHERE type = 'table' AND name = ?;
        #    """,
        #    (table_name,),
        #)

        #if cursor.fetchone() is None:
        #    raise ValueError(f"Table does not exist: {table_name}")

        # Safely quote table name
        #quoted_table_name = '"' + table_name.replace('"', '""') + '"'

        cursor.execute(f"DELETE FROM {table_name};")

        #if reset_autoincrement:
        #    cursor.execute(
        #        "DELETE FROM sqlite_sequence WHERE name = ?;",
        #        (table_name,),
        #    )

        conn.commit()

    print(f"Deleted all rows from table: {table_name}")























