from pathlib import Path
import sqlite3
import pandas as pd


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