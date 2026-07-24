from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

DISEASE_COLUMNS = [
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
    "support_devices",
]


POPULATIONS = [
    {
        "population": "kvp=90, detector=direct, view=AP",
        "kvp": 90,
        "detector_type_code": "direct",
        "view_code": "AP",
    },
    {
        "population": "kvp=110, detector=direct, view=PA",
        "kvp": 110,
        "detector_type_code": "direct",
        "view_code": "PA",
    },
    {
        "population": "kvp=120, detector=scintillator, view=PA",
        "kvp": 120,
        "detector_type_code": "scintillator",
        "view_code": "PA",
    },
]


def summarize_image_acquisition(db_path: Path) -> dict[str, pd.DataFrame]:
    """
    Summarize image acquisition statistics:
    1) total number of images
    2) number of AP / PA images
    3) kVp distribution:
       <90, =90, >90 and <120, =120, >120
    4) same kVp distribution separately for AP and PA views

    Returns
    -------
    dict[str, pd.DataFrame]
        Dictionary with summary tables.
    """

    db_path = Path(db_path)

    queries = {
        "total_images": """
            SELECT COUNT(*) AS total_images
            FROM images;
        """,

        "view_counts": """
            SELECT
                UPPER(ia.view_code) AS view_code,
                COUNT(*) AS image_count
            FROM images img
            JOIN image_acquisition ia
                ON img.image_id = ia.image_id
            WHERE UPPER(ia.view_code) IN ('AP', 'PA')
            GROUP BY UPPER(ia.view_code)
            ORDER BY view_code;
        """,

        "kvp_counts": """
            SELECT
                CASE
                    WHEN ia.kvp < 90 THEN '<90'
                    WHEN ia.kvp = 90 THEN '=90'
                    WHEN ia.kvp > 90 AND ia.kvp < 120 THEN '>90 and <120'
                    WHEN ia.kvp = 120 THEN '=120'
                    WHEN ia.kvp > 120 THEN '>120'
                    ELSE 'missing'
                END AS kvp_group,
                COUNT(*) AS image_count
            FROM images img
            JOIN image_acquisition ia
                ON img.image_id = ia.image_id
            GROUP BY kvp_group
            ORDER BY
                CASE kvp_group
                    WHEN '<90' THEN 1
                    WHEN '=90' THEN 2
                    WHEN '>90 and <120' THEN 3
                    WHEN '=120' THEN 4
                    WHEN '>120' THEN 5
                    WHEN 'missing' THEN 6
                END;
        """,

        "kvp_counts_by_view": """
            SELECT
                UPPER(ia.view_code) AS view_code,
                CASE
                    WHEN ia.kvp < 90 THEN '<90'
                    WHEN ia.kvp = 90 THEN '=90'
                    WHEN ia.kvp > 90 AND ia.kvp < 120 THEN '>90 and <120'
                    WHEN ia.kvp = 120 THEN '=120'
                    WHEN ia.kvp > 120 THEN '>120'
                    ELSE 'missing'
                END AS kvp_group,
                COUNT(*) AS image_count
            FROM images img
            JOIN image_acquisition ia
                ON img.image_id = ia.image_id
            WHERE UPPER(ia.view_code) IN ('AP', 'PA')
            GROUP BY UPPER(ia.view_code), kvp_group
            ORDER BY
                view_code,
                CASE kvp_group
                    WHEN '<90' THEN 1
                    WHEN '=90' THEN 2
                    WHEN '>90 and <120' THEN 3
                    WHEN '=120' THEN 4
                    WHEN '>120' THEN 5
                    WHEN 'missing' THEN 6
                END;
        """
    }

    results = {}

    with sqlite3.connect(db_path) as conn:
        for name, query in queries.items():
            results[name] = pd.read_sql_query(query, conn)

    return results

def print_image_acquisition_summary(summary: dict) -> None:
    """
    Pretty-print image acquisition summary returned by summarize_image_acquisition().
    """

    total_images = int(summary["total_images"]["total_images"].iloc[0])

    print("=" * 60)
    print("IMAGE ACQUISITION SUMMARY")
    print("=" * 60)

    print(f"\nTotal number of images: {total_images:,}")

    print("\nView counts")
    print("-" * 60)
    view_df = summary["view_counts"].copy()
    view_df["percent"] = view_df["image_count"] / total_images * 100

    for _, row in view_df.iterrows():
        print(
            f"{row['view_code']:>5}: "
            f"{int(row['image_count']):>8,} "
            f"({row['percent']:>5.1f}%)"
        )

    print("\nkVp counts")
    print("-" * 60)
    kvp_df = summary["kvp_counts"].copy()
    kvp_df["percent"] = kvp_df["image_count"] / total_images * 100

    for _, row in kvp_df.iterrows():
        print(
            f"{row['kvp_group']:>14}: "
            f"{int(row['image_count']):>8,} "
            f"({row['percent']:>5.1f}%)"
        )

    print("\nkVp counts by view")
    print("-" * 60)

    kvp_by_view_df = summary["kvp_counts_by_view"].copy()

    for view_code, group_df in kvp_by_view_df.groupby("view_code"):
        view_total = int(group_df["image_count"].sum())

        print(f"\nView: {view_code}")
        print(f"Total: {view_total:,}")

        for _, row in group_df.iterrows():
            percent = row["image_count"] / view_total * 100

            print(
                f"  {row['kvp_group']:>14}: "
                f"{int(row['image_count']):>8,} "
                f"({percent:>5.1f}%)"
            )

    print("\n" + "=" * 60)


def get_view_counts(db_path: Path) -> pd.DataFrame:
    """
    Counts the number of images for each view type.

    Parameters
    ----------
    db_path : Path
        Path to SQLite database.

    Returns
    -------
    pd.DataFrame
        Table with view_code, image_count, and percent.
    """

    query = """
        SELECT
            COALESCE(NULLIF(TRIM(view_code), ''), 'missing') AS view_code,
            COUNT(*) AS image_count,
            ROUND(
                100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
                2
            ) AS percent
        FROM image_acquisition
        GROUP BY COALESCE(NULLIF(TRIM(view_code), ''), 'missing')
        ORDER BY image_count DESC;
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    return df


def print_view_counts(view_counts: pd.DataFrame) -> None:
    """
    Prints image counts by view type.

    Parameters
    ----------
    view_counts : pd.DataFrame
        Output of get_view_counts().
    """

    print("\nImage counts by view type")
    print("-" * 40)

    for _, row in view_counts.iterrows():
        print(
            f"{row['view_code']:>12}: "
            f"{row['image_count']:>8} images "
            f"({row['percent']:>6.2f}%)"
        )

    print("-" * 40)
    print(f"{'total':>12}: {view_counts['image_count'].sum():>8} images")


def get_detector_type_counts(db_path: str | Path) -> pd.DataFrame:
    """
    Count images by detector_type_code.
    """

    query = """
        SELECT
            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing') AS detector_type_code,
            COUNT(*) AS image_count
        FROM image_acquisition
        GROUP BY COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing')
        ORDER BY image_count DESC;
    """

    with sqlite3.connect(Path(db_path)) as conn:
        detector_type_counts = pd.read_sql_query(query, conn)

    return detector_type_counts


def print_detector_type_counts(detector_type_counts: pd.DataFrame) -> None:
    """
    Print detector_type_code counts.
    """

    print("\nDetector type counts:")
    print(detector_type_counts.to_string(index=False))



def get_kvp_by_detector_table(db_path: str | Path) -> pd.DataFrame:
    """
    Count images by KVP group and detector_type_code.

    Rows:
        KVP groups

    Columns:
        detector_type_code values, e.g. DIRECT / SCINTILLATOR

    Values:
        image counts
    """

    query = """
        SELECT
            CASE
                WHEN kvp IS NULL THEN 'missing'
                WHEN kvp < 90 THEN '<90'
                WHEN kvp = 90 THEN '=90'
                WHEN kvp > 90 AND kvp < 110 THEN '>90 and <110'
                WHEN kvp = 110 THEN '=110'
                WHEN kvp > 110 AND kvp < 120 THEN '>110 and <120'
                WHEN kvp = 120 THEN '=120'
                WHEN kvp > 120 THEN '>120'
                ELSE 'other'
            END AS kvp_group,

            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing') AS detector_type_code,

            COUNT(*) AS image_count

        FROM image_acquisition

        GROUP BY
            CASE
                WHEN kvp IS NULL THEN 'missing'
                WHEN kvp < 90 THEN '<90'
                WHEN kvp = 90 THEN '=90'
                WHEN kvp > 90 AND kvp < 110 THEN '>90 and <110'
                WHEN kvp = 110 THEN '=110'
                WHEN kvp > 110 AND kvp < 120 THEN '>110 and <120'
                WHEN kvp = 120 THEN '=120'
                WHEN kvp > 120 THEN '>120'
                ELSE 'other'
            END,
            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing');
    """

    with sqlite3.connect(Path(db_path)) as conn:
        df = pd.read_sql_query(query, conn)

    table = df.pivot_table(
        index="kvp_group",
        columns="detector_type_code",
        values="image_count",
        fill_value=0,
        aggfunc="sum",
    )

    kvp_order = [
        "<90",
        "=90",
        ">90 and <110",
        "=110",
        ">110 and <120",
        "=120",
        ">120",
        "missing",
        "other",
    ]

    table = table.reindex(kvp_order)
    table = table.dropna(how="all")
    table = table.astype(int)

    return table


def print_kvp_by_detector_table(table: pd.DataFrame) -> None:
    """
    Print KVP-by-detector contingency table.
    """

    print("\nKVP by detector type:")
    print(table.to_string())

def get_kvp_by_detector_table_for_ap_pa(db_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Compute KVP-by-detector tables separately for AP and PA views.

    Rows:
        KVP groups

    Columns:
        detector_type_code values

    Values:
        image counts
    """

    query = """
        SELECT
            COALESCE(NULLIF(TRIM(view_code), ''), 'missing') AS view_code,

            CASE
                WHEN kvp IS NULL THEN 'missing'
                WHEN kvp < 90 THEN '<90'
                WHEN kvp = 90 THEN '=90'
                WHEN kvp > 90 AND kvp < 110 THEN '>90 and <110'
                WHEN kvp = 110 THEN '=110'
                WHEN kvp > 110 AND kvp < 120 THEN '>110 and <120'
                WHEN kvp = 120 THEN '=120'
                WHEN kvp > 120 THEN '>120'
                ELSE 'other'
            END AS kvp_group,

            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing') AS detector_type_code,

            COUNT(*) AS image_count

        FROM image_acquisition

        WHERE TRIM(view_code) IN ('AP', 'PA')

        GROUP BY
            COALESCE(NULLIF(TRIM(view_code), ''), 'missing'),
            CASE
                WHEN kvp IS NULL THEN 'missing'
                WHEN kvp < 90 THEN '<90'
                WHEN kvp = 90 THEN '=90'
                WHEN kvp > 90 AND kvp < 110 THEN '>90 and <110'
                WHEN kvp = 110 THEN '=110'
                WHEN kvp > 110 AND kvp < 120 THEN '>110 and <120'
                WHEN kvp = 120 THEN '=120'
                WHEN kvp > 120 THEN '>120'
                ELSE 'other'
            END,
            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing');
    """

    kvp_order = [
        "<90",
        "=90",
        ">90 and <110",
        "=110",
        ">110 and <120",
        "=120",
        ">120",
        "missing",
        "other",
    ]

    with sqlite3.connect(Path(db_path)) as conn:
        df = pd.read_sql_query(query, conn)

    result = {}

    for view in ["AP", "PA"]:
        view_df = df[df["view_code"] == view]

        table = view_df.pivot_table(
            index="kvp_group",
            columns="detector_type_code",
            values="image_count",
            fill_value=0,
            aggfunc="sum",
        )

        table = table.reindex(kvp_order)
        table = table.dropna(how="all")
        table = table.astype(int)

        result[view] = table

    return result

def print_kvp_by_detector_table_for_ap_pa(tables: dict[str, pd.DataFrame]) -> None:
    """
    Print KVP-by-detector tables for AP and PA views.
    """

    for view, table in tables.items():
        print("\n" + "=" * 40)
        print(f"KVP by detector type for {view} view")
        print("=" * 40)

        if table.empty:
            print("No data.")
        else:
            print(table.to_string())


KVP_GROUP_ORDER = [
    "<90",
    "=90",
    ">90 and <110",
    "=110",
    ">110 and <120",
    "=120",
    ">120",
    "missing",
]

DETECTOR_TYPE_ORDER = [
    "DIRECT",
    "SCINTILLATOR",
    "missing",
]


def format_kvp_by_detector_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert long-format table:

        detector_type_code | kvp_group | image_count

    into wide-format table:

        kvp_group | DIRECT | SCINTILLATOR | missing
    """

    if df.empty:
        return pd.DataFrame(
            {
                "kvp_group": KVP_GROUP_ORDER,
                "DIRECT": 0,
                "SCINTILLATOR": 0,
                "missing": 0,
            }
        )

    table = (
        df.pivot_table(
            index="kvp_group",
            columns="detector_type_code",
            values="image_count",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    # Ensure all detector columns exist
    for detector_type in DETECTOR_TYPE_ORDER:
        if detector_type not in table.columns:
            table[detector_type] = 0

    # Ensure all kVp groups exist, even if count is zero
    all_kvp_groups = pd.DataFrame({"kvp_group": KVP_GROUP_ORDER})

    table = all_kvp_groups.merge(
        table,
        on="kvp_group",
        how="left",
    )

    # Fill missing values after merge
    for detector_type in DETECTOR_TYPE_ORDER:
        table[detector_type] = table[detector_type].fillna(0).astype(int)

    table = table[["kvp_group"] + DETECTOR_TYPE_ORDER]

    return table


def get_kvp_by_detector_table_for_lateral(
    db_path: str | Path,
) -> pd.DataFrame:
    """
    Compute kVp distribution by detector type for lateral views.

    Returns table in wide format:

        kvp_group | DIRECT | SCINTILLATOR | missing
    """

    query = """
        SELECT
            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing') AS detector_type_code,
            CASE
                WHEN kvp IS NULL THEN 'missing'
                WHEN kvp < 90 THEN '<90'
                WHEN kvp = 90 THEN '=90'
                WHEN kvp > 90 AND kvp < 110 THEN '>90 and <110'
                WHEN kvp = 110 THEN '=110'
                WHEN kvp > 110 AND kvp < 120 THEN '>110 and <120'
                WHEN kvp = 120 THEN '=120'
                WHEN kvp > 120 THEN '>120'
                ELSE 'missing'
            END AS kvp_group,
            COUNT(*) AS image_count
        FROM image_acquisition
        WHERE UPPER(TRIM(view_code)) = 'LATERAL'
        GROUP BY detector_type_code, kvp_group
        ORDER BY detector_type_code, kvp_group;
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    return format_kvp_by_detector_table(df)

def get_kvp_by_detector_table_for_ll(
    db_path: str | Path,
) -> pd.DataFrame:
    """
    Compute kVp distribution by detector type for LL views.

    Returns table in wide format:

        kvp_group | DIRECT | SCINTILLATOR | missing
    """

    query = """
        SELECT
            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing') AS detector_type_code,
            CASE
                WHEN kvp IS NULL THEN 'missing'
                WHEN kvp < 90 THEN '<90'
                WHEN kvp = 90 THEN '=90'
                WHEN kvp > 90 AND kvp < 110 THEN '>90 and <110'
                WHEN kvp = 110 THEN '=110'
                WHEN kvp > 110 AND kvp < 120 THEN '>110 and <120'
                WHEN kvp = 120 THEN '=120'
                WHEN kvp > 120 THEN '>120'
                ELSE 'missing'
            END AS kvp_group,
            COUNT(*) AS image_count
        FROM image_acquisition
        WHERE UPPER(TRIM(view_code)) = 'LL'
        GROUP BY detector_type_code, kvp_group
        ORDER BY detector_type_code, kvp_group;
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    return format_kvp_by_detector_table(df)


def get_kvp_by_detector_table_for_missing_view(
    db_path: str | Path,
) -> pd.DataFrame:
    """
    Compute kVp distribution by detector type for images with missing view code.

    Returns table in wide format:

        kvp_group | DIRECT | SCINTILLATOR | missing
    """

    query = """
        SELECT
            COALESCE(NULLIF(TRIM(detector_type_code), ''), 'missing') AS detector_type_code,
            CASE
                WHEN kvp IS NULL THEN 'missing'
                WHEN kvp < 90 THEN '<90'
                WHEN kvp = 90 THEN '=90'
                WHEN kvp > 90 AND kvp < 110 THEN '>90 and <110'
                WHEN kvp = 110 THEN '=110'
                WHEN kvp > 110 AND kvp < 120 THEN '>110 and <120'
                WHEN kvp = 120 THEN '=120'
                WHEN kvp > 120 THEN '>120'
                ELSE 'missing'
            END AS kvp_group,
            COUNT(*) AS image_count
        FROM image_acquisition
        WHERE view_code IS NULL
           OR TRIM(view_code) = ''
        GROUP BY detector_type_code, kvp_group
        ORDER BY detector_type_code, kvp_group;
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    return format_kvp_by_detector_table(df)


def print_table_names(db_path: str | Path) -> None:
    db_path = Path(db_path)

    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
    """

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query)
        table_names = cursor.fetchall()

    for (table_name,) in table_names:
        print(table_name)

def print_row_counts_for_tables(db_path: str | Path) -> None:
    db_path = Path(db_path)

    table_names = [
        "chexpert_diagnosis",
        "chexpert_diagnosisi",
    ]

    with sqlite3.connect(db_path) as conn:
        for table_name in table_names:
            query = f'SELECT COUNT(*) FROM "{table_name}";'
            row_count = conn.execute(query).fetchone()[0]
            print(f"{table_name}: {row_count}")



def get_chexpert_population_statistics(
    db_path: str | Path,
    populations: list[dict] = POPULATIONS,
    disease_columns: list[str] = DISEASE_COLUMNS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute CheXpert label statistics for selected acquisition populations.

    Returns
    -------
    population_summary_df:
        One row per population with:
            population
            unique_patients
            image_count

    label_statistics_df:
        One row per population and disease with:
            population
            disease
            label_0_count
            label_1_count
            label_minus_1_count
    """

    db_path = Path(db_path)

    summary_rows = []
    label_rows = []

    with sqlite3.connect(db_path) as conn:
        for pop in populations:
            population_name = pop["population"]
            kvp = pop["kvp"]
            detector_type_code = pop["detector_type_code"]
            view_code = pop["view_code"]

            summary_query = """
                SELECT
                    COUNT(DISTINCT s.subject_id) AS unique_patients,
                    COUNT(DISTINCT i.image_id) AS image_count
                FROM chexpert_diagnosis AS cd
                INNER JOIN images AS i
                    ON cd.study_id = i.study_id
                INNER JOIN studies AS s
                    ON cd.study_id = s.study_id
                INNER JOIN image_acquisition AS ia
                    ON i.image_id = ia.image_id
                WHERE ia.kvp = ?
                  AND LOWER(TRIM(ia.detector_type_code)) = LOWER(TRIM(?))
                  AND UPPER(TRIM(ia.view_code)) = UPPER(TRIM(?));
            """

            summary_df = pd.read_sql_query(
                summary_query,
                conn,
                params=(kvp, detector_type_code, view_code),
            )

            summary_rows.append(
                {
                    "population": population_name,
                    "unique_patients": int(summary_df.loc[0, "unique_patients"]),
                    "image_count": int(summary_df.loc[0, "image_count"]),
                }
            )

            for disease in disease_columns:
                label_query = f"""
                    SELECT
                        SUM(CASE WHEN cd."{disease}" = 0 THEN 1 ELSE 0 END) AS label_0_count,
                        SUM(CASE WHEN cd."{disease}" = 1 THEN 1 ELSE 0 END) AS label_1_count,
                        SUM(CASE WHEN cd."{disease}" = -1 THEN 1 ELSE 0 END) AS label_minus_1_count
                    FROM chexpert_diagnosis AS cd
                    INNER JOIN images AS i
                        ON cd.study_id = i.study_id
                    INNER JOIN studies AS s
                        ON cd.study_id = s.study_id
                    INNER JOIN image_acquisition AS ia
                        ON i.image_id = ia.image_id
                    WHERE ia.kvp = ?
                      AND LOWER(TRIM(ia.detector_type_code)) = LOWER(TRIM(?))
                      AND UPPER(TRIM(ia.view_code)) = UPPER(TRIM(?));
                """

                label_df = pd.read_sql_query(
                    label_query,
                    conn,
                    params=(kvp, detector_type_code, view_code),
                )

                label_rows.append(
                    {
                        "population": population_name,
                        "disease": disease,
                        "label_0_count": int(label_df.loc[0, "label_0_count"] or 0),
                        "label_1_count": int(label_df.loc[0, "label_1_count"] or 0),
                        "label_minus_1_count": int(label_df.loc[0, "label_minus_1_count"] or 0),
                    }
                )

    population_summary_df = pd.DataFrame(summary_rows)
    label_statistics_df = pd.DataFrame(label_rows)

    return population_summary_df, label_statistics_df


def print_chexpert_population_statistics(
    population_summary_df: pd.DataFrame,
    label_statistics_df: pd.DataFrame,
) -> None:
    """
    Print population-level and disease-level statistics.
    """

    for population in population_summary_df["population"]:
        print("=" * 80)
        print(population)
        print("=" * 80)

        summary_row = population_summary_df[
            population_summary_df["population"] == population
        ].iloc[0]

        print(f"Unique patients: {summary_row['unique_patients']}")
        print(f"Images:          {summary_row['image_count']}")
        print()

        disease_df = label_statistics_df[
            label_statistics_df["population"] == population
        ].copy()

        disease_df = disease_df[
            [
                "disease",
                "label_0_count",
                "label_1_count",
                "label_minus_1_count",
            ]
        ]

        print(disease_df.to_string(index=False))
        print()


def get_exposure_mas_for_three_populations(
    db_path: str | Path,
) -> pd.DataFrame:
    """
    Extract exposure_mas values for three acquisition populations:

        1. DIRECT, kVp = 90
        2. DIRECT, kVp = 110
        3. SCINTILLATOR, kVp = 120

    Returns
    -------
    pd.DataFrame
        Columns:
            detector_type_code
            kvp
            exposure_mas
            population
    """

    query = """
        SELECT
            detector_type_code,
            kvp,
            exposure_mas
        FROM image_acquisition
        WHERE
            exposure_mas IS NOT NULL
            AND (
                (UPPER(TRIM(detector_type_code)) = 'DIRECT' AND kvp = 90)
                OR
                (UPPER(TRIM(detector_type_code)) = 'DIRECT' AND kvp = 110)
                OR
                (UPPER(TRIM(detector_type_code)) = 'SCINTILLATOR' AND kvp = 120)
            )
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    df["detector_type_code"] = df["detector_type_code"].str.upper().str.strip()

    df["population"] = (
        df["detector_type_code"]
        + ", kVp="
        + df["kvp"].astype(int).astype(str)
    )

    return df



def plot_exposure_mas_histograms_for_three_populations(
    mas_df: pd.DataFrame,
    max_x: int = 25,
) -> None:
    """
    Plot independently normalized exposure_mas histograms for:

        DIRECT, kVp=90
        DIRECT, kVp=110
        SCINTILLATOR, kVp=120

    Each bin shows:

        number of images in the bin / total number of images in the population

    Therefore, if all values are within [0, max_x], the sum of bins is 1.

    Values > max_x are not corrected here. A message is printed instead.
    """

    populations = [
        "DIRECT, kVp=90",
        "DIRECT, kVp=110",
        "SCINTILLATOR, kVp=120",
    ]

    # Bin edges: 0, 1, 2, ..., 25
    # This gives 25 bins:
    # [0,1), [1,2), ..., [24,25]
    bin_edges = np.arange(0, max_x + 1, 1)

    fig, axes = plt.subplots(
        nrows=1,
        ncols=3,
        figsize=(18, 5),
        sharey=True,
    )

    for ax, population in zip(axes, populations):
        values = mas_df.loc[
            mas_df["population"] == population,
            "exposure_mas"
        ].dropna()

        total_n = len(values)

        if total_n == 0:
            ax.set_title(f"{population}\nN = 0")
            ax.set_xlabel("Exposure mAs")
            ax.set_ylabel("Ratio")
            ax.set_xlim(0, max_x)
            ax.set_ylim(0, 1)
            continue

        out_of_range_n = (values > max_x).sum()

        if out_of_range_n > 0:
            print(
                f"{population}: {out_of_range_n} images have "
                f"exposure_mas > {max_x} and are outside the plotting range."
            )

        values_for_plot = values[values <= max_x]

        counts, _ = np.histogram(
            values_for_plot,
            bins=bin_edges,
        )

        # Normalize by total population size
        ratios = counts / total_n

        ax.bar(
            bin_edges[:-1],
            ratios,
            width=1.0,
            align="edge",
            edgecolor="black",
            alpha=0.75,
        )

        ax.set_title(
            f"{population}\n"
            f"N = {total_n}, outside range = {out_of_range_n}"
        )
        ax.set_xlabel("Exposure mAs")
        ax.set_xlim(0, max_x)
        ax.set_ylim(0, 1)

        ax.set_xticks(np.arange(0, max_x + 1, 5))

        ax.set_ylabel("Ratio")

    plt.tight_layout()
    plt.show()


def population_mAs_statistics(
        mas_df: pd.DataFrame
        )-> pd.DataFrame:
        
    mas_df_d110 = mas_df[mas_df["population"] == "DIRECT, kVp=110"]
    mean_d110 = mas_df_d110['exposure_mas'].mean()
    sdev_d110 = mas_df_d110['exposure_mas'].std()

    mas_df_d90 = mas_df[mas_df["population"] == "DIRECT, kVp=90"]
    mean_d90 = mas_df_d90['exposure_mas'].mean()
    sdev_d90 = mas_df_d90['exposure_mas'].std()

    mas_df_s120 = mas_df[mas_df["population"] == "DIRECT, kVp=110"]
    mean_s120 = mas_df_s120['exposure_mas'].mean()
    sdev_s120 = mas_df_s120['exposure_mas'].std()

    summary_df = pd.DataFrame({
        "population": [
            "DIRECT, kVp=90",
            "DIRECT, kVp=110",
            "SCINTILLATOR, kVp=120",
        ],
        "mean_exposure_mas": [
            mean_d90,
            mean_d110,
            mean_s120,
        ],
        "std_exposure_mas": [
            sdev_d90,
            sdev_d110,
            sdev_s120,
        ],
    }).round(2)

    return summary_df



