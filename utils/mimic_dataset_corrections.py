from pathlib import Path
import shutil
import tempfile
import sqlite3

import pandas as pd


def clean_microbiologyevents_csv_inplace(
    csv_path: Path,
    chunksize: int = 100_000,
    create_backup: bool = True,
) -> None:
    """
    Cleans microbiologyevents CSV in-place.

    Removes rows where any NOT NULL column has a null-like value:
    "", "nil", "nill", "null", "none", "nan"

    The original file is overwritten.
    Optionally creates a .bak backup before overwriting.
    """

    csv_path = Path(csv_path)

    not_null_columns = [
        "microevent_id",
        "subject_id",
        "micro_specimen_id",
        "chartdate",
        "spec_itemid",
        "spec_type_desc",
        "test_seq",
    ]

    null_like_values = {"", "nil", "nill", "null", "none", "nan"}

    if create_backup:
        backup_path = csv_path.with_suffix(csv_path.suffix + ".bak")
        shutil.copy2(csv_path, backup_path)
        print(f"Backup created: {backup_path}")

    total_rows = 0
    removed_rows = 0
    kept_rows = 0
    first_chunk = True

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        delete=False,
        newline="",
        encoding="utf-8",
        dir=csv_path.parent,
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        for chunk in pd.read_csv(
            csv_path,
            chunksize=chunksize,
            dtype=str,
            keep_default_na=False,
        ):
            missing_columns = [
                col for col in not_null_columns
                if col not in chunk.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns in CSV: {missing_columns}"
                )

            total_rows += len(chunk)

            mask_remove = pd.Series(False, index=chunk.index)

            for col in not_null_columns:
                normalized = chunk[col].str.strip().str.lower()
                mask_remove |= normalized.isin(null_like_values)

            removed_rows += int(mask_remove.sum())

            clean_chunk = chunk.loc[~mask_remove]
            kept_rows += len(clean_chunk)

            clean_chunk.to_csv(
                tmp_path,
                mode="w" if first_chunk else "a",
                index=False,
                header=first_chunk,
                encoding="utf-8",
            )

            first_chunk = False

        shutil.move(tmp_path, csv_path)

        print(f"Cleaned file overwritten: {csv_path}")
        print(f"Total rows: {total_rows}")
        print(f"Removed rows: {removed_rows}")
        print(f"Kept rows: {kept_rows}")

    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


from pathlib import Path
import shutil
import tempfile

import pandas as pd




def clean_prescriptions_required_columns_inplace(
    csv_path: Path,
    chunksize: int = 100_000,
    create_backup: bool = True,
) -> None:
    """
    Clean prescriptions CSV in-place.

    Removes rows where any required column has a null-like value.

    Required columns:
        subject_id, hadm_id, pharmacy_id, drug_type, drug

    Null-like values:
        "", "nil", "nill", "null", "none", "nan", "na", "n/a"

    The original CSV file is overwritten.
    """

    csv_path = Path(csv_path)

    required_columns = [
        "subject_id",
        "hadm_id",
        "pharmacy_id",
        "drug_type",
        "drug",
    ]

    null_like_values = {
        "",
        "nil",
        "nill",
        "null",
        "none",
        "nan",
        "na",
        "n/a",
    }

    if create_backup:
        backup_path = csv_path.with_suffix(csv_path.suffix + ".bak")
        shutil.copy2(csv_path, backup_path)
        print(f"Backup created: {backup_path}")

    total_rows = 0
    removed_rows = 0
    kept_rows = 0

    removed_by_column = {
        col: 0 for col in required_columns
    }

    first_chunk = True

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        delete=False,
        newline="",
        encoding="utf-8",
        dir=csv_path.parent,
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        for chunk in pd.read_csv(
            csv_path,
            chunksize=chunksize,
            dtype=str,
            keep_default_na=False,
        ):
            missing_columns = [
                col for col in required_columns
                if col not in chunk.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns in CSV: {missing_columns}"
                )

            total_rows += len(chunk)

            remove_mask = pd.Series(False, index=chunk.index)

            for col in required_columns:
                normalized = chunk[col].str.strip().str.lower()
                col_bad_mask = normalized.isin(null_like_values)

                removed_by_column[col] += int(col_bad_mask.sum())
                remove_mask |= col_bad_mask

            clean_chunk = chunk.loc[~remove_mask]

            removed_rows += int(remove_mask.sum())
            kept_rows += len(clean_chunk)

            clean_chunk.to_csv(
                tmp_path,
                mode="w" if first_chunk else "a",
                index=False,
                header=first_chunk,
                encoding="utf-8",
            )

            first_chunk = False

        shutil.move(tmp_path, csv_path)

        print(f"Cleaned file overwritten: {csv_path}")
        print(f"Total rows: {total_rows}")
        print(f"Removed rows: {removed_rows}")
        print(f"Kept rows: {kept_rows}")

        print("\nRemoved by column:")
        for col, count in removed_by_column.items():
            print(f"  {col}: {count}")

    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise



def check_csv_study_id_match(
        diagnosis_path:Path,
        list_csv_path:Path,
        missing_pid_csv_path:Path
        ) ->  list[int] | set[int]:
    
    diagnosis_csv = pd.read_csv(diagnosis_path)
    diagnosis_subject_id = set(diagnosis_csv['subject_id'])
    list_csv = pd.read_csv(list_csv_path)
    list_csv_subject_id = set(list_csv['subject_id'])
    missing = list_csv_subject_id - diagnosis_subject_id
    print(f'There are {len(missing)} missing PIDs')
    if len(missing) > 0:
        missing_df = pd.DataFrame(
            {
                "subject_id": sorted(missing)
            }
        )
        missing_pid_csv_path.parent.mkdir(parents=True, exist_ok=True)

        missing_df.to_csv(
            missing_pid_csv_path,
            index=False,
        )
    return missing
    


def insert_missing_subject_ids(
    db_path: Path,
    missing_subject_ids_path: Path,
) -> None:
    """
    Insert missing subject_id values into patients table.
    Other columns will be NULL.
    """
    
    missing_df = pd.read_csv(missing_subject_ids_path)

    if "subject_id" not in missing_df.columns:
        raise ValueError(
            f"Column 'subject_id' not found in {missing_subject_ids_path}"
        )

    subject_ids = (
        missing_df["subject_id"]
        .dropna()
        .astype(int)
        .tolist()
    )

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        for subject_id in subject_ids:
            cursor.execute(
                """
                INSERT OR IGNORE INTO patients (subject_id)
                VALUES (?);
                """,
                (subject_id,),
            )

        conn.commit()