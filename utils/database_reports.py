from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Mapping, Sequence
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from utils.templates_split import (
    BinaryClassDatasetReadError,
    BinaryClassDatasetSplitStatistic
)

from .experiments_metadata import DatasetReportMetadata

def dataframe_to_reportlab_table(df: pd.DataFrame) -> Table:
    """
    Convert pandas DataFrame to ReportLab table.
    """

    df_to_print = df.copy()

    # If index contains meaningful row labels, keep it as first column
    if df_to_print.index.name is not None or not isinstance(df_to_print.index, pd.RangeIndex):
        df_to_print = df_to_print.reset_index()

    data = [list(df_to_print.columns)] + df_to_print.astype(str).values.tolist()

    table = Table(data, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ]
        )
    )

    return table



def make_table_block(
    table_title: str,
    df: pd.DataFrame,
    styles,
):
    """
    Create one visual block:
    title + dataframe table.
    """

    block = [
        Paragraph(table_title, styles["Heading2"]),
        Spacer(1, 0.15 * cm),
    ]

    if df.empty:
        block.append(Paragraph("No data.", styles["Normal"]))
    else:
        block.append(dataframe_to_reportlab_table(df))

    return block


def generate_aquisition_pdf_report(
    output_pdf_path: str | Path,
    tables: dict[str, pd.DataFrame],
    title: str = "X-ray Acquisition Statistics Report",
) -> None:
    """
    Generate PDF report from multiple pandas DataFrames.

    Tables are arranged in two-column blocks:
    left table, right table, then next row.
    """

    output_pdf_path = Path(output_pdf_path)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    # Available page width
    page_width, page_height = landscape(A4)
    usable_width = page_width - doc.leftMargin - doc.rightMargin

    gap = 0.5 * cm
    col_width = (usable_width - gap) / 2

    #################################################
    #       View counts AND Detector Types
    #################################################
    
    leftA = tables['View counts']
    rightA = tables['Detector Types']

    left_block = make_table_block(
            table_title='View counts',
            df=leftA,
            styles=styles,
        )

    right_block = make_table_block(
                table_title='Detector Types',
                df=rightA,
                styles=styles,
         
        )
    gutter_width = 1.2 * cm
    col_width = (usable_width - gutter_width) / 2

    row_table = Table(
        [[left_block, "", right_block]],
        colWidths=[col_width, gutter_width, col_width],
        hAlign="LEFT",
    )

    row_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),

                    # Add space between left and right columns
                    ("RIGHTPADDING", (0, 0), (0, 0), gap),
                ]
            )
        )
    
    story.append(row_table)
    story.append(Spacer(1, 0.6 * cm))

    #################################################
    #       kVp BY Detector Type
    #################################################
    
    story.append(Paragraph('KVP by detector type - all views', styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))
    
    df = tables['KVP by detector type - all views']
    
    story.append(dataframe_to_reportlab_table(df))
    story.append(PageBreak())
    

    #################################################
    #       kVp BY Detector Type: AP AND PA views
    #################################################
    
    leftB = tables['KVP by detector type - AP view']
    rightB = tables['KVP by detector type - PA view']

    left_block = make_table_block(
            table_title='KVP by detector type - AP view',
            df=leftB,
            styles=styles,
        )

    right_block = make_table_block(
                table_title='KVP by detector type - PA view',
                df=rightB,
                styles=styles,
         
        )
        
    row_table = Table(
        [[left_block, "", right_block]],
        colWidths=[col_width, gutter_width, col_width],
        hAlign="LEFT",
    )

    row_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),

                    # Add space between left and right columns
                    ("RIGHTPADDING", (0, 0), (0, 0), gap),
                ]
            )
        )
    
    story.append(row_table)
    
    #################################################
    #       kVp BY Detector Type: lateral AND LL views
    #################################################
    
    leftB = tables['KVP by detector type - Lateral view']
    rightB = tables['KVP by detector type - LL view']

    left_block = make_table_block(
            table_title='KVP by detector type - Lateral view',
            df=leftB,
            styles=styles,
        )

    right_block = make_table_block(
                table_title='KVP by detector type - LL view',
                df=rightB,
                styles=styles,
         
        )
        
    row_table = Table(
        [[left_block, "", right_block]],
        colWidths=[col_width, gutter_width, col_width],
        hAlign="LEFT",
    )

    row_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),

                    # Add space between left and right columns
                    ("RIGHTPADDING", (0, 0), (0, 0), gap),
                ]
            )
        )

    story.append(row_table)
    story.append(PageBreak())

    #################################################
    #       kVp BY Detector Type: Missing view
    #################################################
    
    story.append(Paragraph('KVP by detector type - Missing view', styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))
    
    df = tables['KVP by detector type - Missing view']
    
    story.append(dataframe_to_reportlab_table(df))


    #################################################
    #       mAs Standard Deviation by Population
    #################################################
    
    story.append(Paragraph('mAs Standard Deviation by Population', styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))
    
    df = tables['mAs Standard Deviation by Population']
    
    story.append(dataframe_to_reportlab_table(df))
        

    doc.build(story)

    print(f"PDF report saved to: {output_pdf_path}")



def _format_column_name(column_name: str) -> str:
    """
    Convert snake_case column names to readable report labels.
    """
    return column_name.replace("_", " ").title()


def _dataframe_to_reportlab_table(
    df: pd.DataFrame,
    column_widths: list[float] | None = None,
) -> Table:
    """
    Convert a pandas DataFrame into a ReportLab table.
    """

    table_data = []

    header = [_format_column_name(col) for col in df.columns]
    table_data.append(header)

    for _, row in df.iterrows():
        table_data.append([str(value) for value in row.values])

    table = Table(
        table_data,
        colWidths=column_widths,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),

                # Body
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),

                # Grid
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),

                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),

                # Vertical alignment
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    return table



def _parse_population_name(population_name: str) -> tuple[str, str, str]:
    """
    Parse population string like:
        kvp=90, detector_type_code=direct, view_code=AP

    Returns
    -------
    kvp, detector, view
    """

    parts = population_name.split(", ")

    kvp = parts[0].split("=")[1]
    detector = parts[1].split("=")[1]
    view = parts[2].split("=")[1]

    return kvp, detector, view


def _format_population_header(
    population_name: str,
    unique_patients: int,
    total_images: int,
) -> str:
    """
    Create multiline table header for one population.
    """

    kvp, detector, view = _parse_population_name(population_name)

    return (
        f"{kvp} keV<br/>"
        f"{detector.title()}<br/>"
        f"{view}<br/>"
        f"Patients: {unique_patients}<br/>"
        f"Images: {total_images}"
    )


def generate_disease_aquisition_pdf_report(
    output_pdf_path: str | Path,
    population_summary_df: pd.DataFrame,
    label_statistics_df: pd.DataFrame,
    title: str = "Diagnostic Summary Report",
) -> None:
    """
    Generate a PDF report for disease information per different acquisition populations.

    Expected population_summary_df columns:
        population
        unique_patients
        image_count

    Expected label_statistics_df columns:
        population
        disease
        label_0_count
        label_1_count
        label_minus_1_count

    The output table has:
        rows    = diseases
        columns = populations
        subcolumns per population = Positive(1), Uncertain(-1)
    """

    output_pdf_path = Path(output_pdf_path)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]

    header_style = ParagraphStyle(
        name="HeaderStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        leading=10,
    )

    disease_style = ParagraphStyle(
        name="DiseaseStyle",
        parent=styles["Normal"],
        alignment=TA_LEFT,
        fontSize=8,
        leading=10,
    )

    cell_style = ParagraphStyle(
        name="CellStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        leading=10,
    )

    story = []

    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5 * cm))

    # Available page width
    page_width, page_height = landscape(A4)
    usable_width = page_width - doc.leftMargin - doc.rightMargin

    # ------------------------------------------------------------------
    # The logic below keeps the same idea:
    # population one   = row 0
    # population two   = row 1
    # population three = row 2
    # ------------------------------------------------------------------

    #################################################
    #       kvp=90, detector=direct, view=AP
    #################################################
    population_one = population_summary_df.iloc[0]["population"]
    unique_patients_one = population_summary_df.iloc[0]["unique_patients"]
    total_images_one = population_summary_df.iloc[0]["image_count"]

    #################################################
    #       kvp=110, detector=direct, view=PA
    #################################################
    population_two = population_summary_df.iloc[1]["population"]
    unique_patients_two = population_summary_df.iloc[1]["unique_patients"]
    total_images_two = population_summary_df.iloc[1]["image_count"]

    #################################################
    #       kvp=120, detector=scintillator, view=PA
    #################################################
    population_three = population_summary_df.iloc[2]["population"]
    unique_patients_three = population_summary_df.iloc[2]["unique_patients"]
    total_images_three = population_summary_df.iloc[2]["image_count"]

    population_one_header = _format_population_header(
        population_one,
        unique_patients_one,
        total_images_one,
    )

    population_two_header = _format_population_header(
        population_two,
        unique_patients_two,
        total_images_two,
    )

    population_three_header = _format_population_header(
        population_three,
        unique_patients_three,
        total_images_three,
    )

    # Disease order is taken from the first population
    disease_names = (
        label_statistics_df[
            label_statistics_df["population"] == population_one
        ]["disease"]
        .tolist()
    )

    # ------------------------------------------------------------------
    # Build table
    # ------------------------------------------------------------------

    table_data = []

    # Header row 1: population groups
    table_data.append(
        [
            "",
            Paragraph(population_one_header, header_style),
            "",
            Paragraph(population_two_header, header_style),
            "",
            Paragraph(population_three_header, header_style),
            "",
        ]
    )

    # Header row 2: positive / uncertain
    table_data.append(
        [
            "",
            Paragraph("Positive(1)", header_style),
            Paragraph("Uncertain(-1)", header_style),
            Paragraph("Positive(1)", header_style),
            Paragraph("Uncertain(-1)", header_style),
            Paragraph("Positive(1)", header_style),
            Paragraph("Uncertain(-1)", header_style),
        ]
    )

    for disease in disease_names:
        pop_one_row = label_statistics_df[
            (label_statistics_df["population"] == population_one)
            & (label_statistics_df["disease"] == disease)
        ].iloc[0]

        pop_two_row = label_statistics_df[
            (label_statistics_df["population"] == population_two)
            & (label_statistics_df["disease"] == disease)
        ].iloc[0]

        pop_three_row = label_statistics_df[
            (label_statistics_df["population"] == population_three)
            & (label_statistics_df["disease"] == disease)
        ].iloc[0]

        table_data.append(
            [
                Paragraph(str(disease), disease_style),

                Paragraph(str(pop_one_row["label_1_count"]), cell_style),
                Paragraph(str(pop_one_row["label_minus_1_count"]), cell_style),

                Paragraph(str(pop_two_row["label_1_count"]), cell_style),
                Paragraph(str(pop_two_row["label_minus_1_count"]), cell_style),

                Paragraph(str(pop_three_row["label_1_count"]), cell_style),
                Paragraph(str(pop_three_row["label_minus_1_count"]), cell_style),
            ]
        )

    disease_col_width = 5.0 * cm
    data_col_width = (usable_width - disease_col_width) / 6

    table = Table(
        table_data,
        colWidths=[
            disease_col_width,
            data_col_width,
            data_col_width,
            data_col_width,
            data_col_width,
            data_col_width,
            data_col_width,
        ],
        repeatRows=2,
    )

    table.setStyle(
        TableStyle(
            [
                # Population group spans
                ("SPAN", (1, 0), (2, 0)),
                ("SPAN", (3, 0), (4, 0)),
                ("SPAN", (5, 0), (6, 0)),

                # Empty disease header cell spans two header rows
                ("SPAN", (0, 0), (0, 1)),

                # Header formatting
                ("BACKGROUND", (0, 0), (-1, 1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, 1), "CENTER"),
                ("VALIGN", (0, 0), (-1, 1), "MIDDLE"),

                # Body formatting
                ("FONTNAME", (0, 2), (-1, -1), "Helvetica"),
                ("ALIGN", (1, 2), (-1, -1), "CENTER"),
                ("ALIGN", (0, 2), (0, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                # Grid
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),

                # Slightly stronger lines between population groups
                ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.grey),
                ("LINEAFTER", (2, 0), (2, -1), 0.5, colors.grey),
                ("LINEAFTER", (4, 0), (4, -1), 0.5, colors.grey),

                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(table)

    doc.build(story)

    print(f"PDF report saved to: {output_pdf_path}")
# ======================================================================
# Binary dataset split report
# ======================================================================

_BINARY_DATASET_ERROR_PATH_LIMIT = 10


def _validate_binary_dataset_report_paths(
    output_paths: Sequence[str | Path],
) -> list[Path]:
    """
    Validate complete output paths for identical PDF copies.

    All paths must be absolute, unique, use the .pdf extension, and
    must not already exist.
    """
    if isinstance(output_paths, (str, Path)):
        raise TypeError(
            "output_paths must be a sequence of complete PDF paths, "
            "not a single path."
        )

    paths = [Path(path).expanduser() for path in output_paths]

    if not paths:
        raise ValueError(
            "output_paths must contain at least one PDF path."
        )

    normalized_paths: set[str] = set()

    for path in paths:
        if not path.is_absolute():
            raise ValueError(
                f"Output path must be absolute: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Output path must have a .pdf extension: {path}"
            )

        normalized_path = os.path.normcase(
            str(path.resolve(strict=False))
        )

        if normalized_path in normalized_paths:
            raise ValueError(
                f"Duplicate output path: {path}"
            )

        normalized_paths.add(normalized_path)

        if path.exists():
            raise FileExistsError(
                f"Output PDF already exists: {path}"
            )

    return paths


def _validate_dataset_report_metadata(
    metadata: DatasetReportMetadata,
) -> None:
    """
    Ensure that every required metadata field contains non-empty text.
    """
    metadata_fields = {
        "title": metadata.title,
        "task_description": metadata.task_description,
        "labeling": metadata.labeling,
        "positive_class_description": (
            metadata.positive_class_description
        ),
        "negative_class_description": (
            metadata.negative_class_description
        ),
        "inclusion_criteria": metadata.inclusion_criteria,
        "exclusion_criteria": metadata.exclusion_criteria,
    }

    for field_name, value in metadata_fields.items():
        if not isinstance(value, str):
            raise TypeError(
                f"metadata.{field_name} must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"metadata.{field_name} must not be empty."
            )


def _get_split_statistic(
    split_report: Mapping[
        BinaryClassDatasetSplitStatistic,
        int,
    ],
    key: BinaryClassDatasetSplitStatistic,
) -> int:
    """
    Read and validate one non-negative split statistic.
    """
    if key not in split_report:
        raise KeyError(
            f"Missing split statistic: {key.value}"
        )

    value = split_report[key]

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"Split statistic {key.value!r} must be an integer."
        )

    if value < 0:
        raise ValueError(
            f"Split statistic {key.value!r} must not be negative."
        )

    return value


def _get_dataset_error_paths(
    error_report: Mapping[
        BinaryClassDatasetReadError,
        Sequence[str],
    ],
    key: BinaryClassDatasetReadError,
) -> list[str]:
    """
    Read one error category and normalize its paths to strings.
    """
    if key not in error_report:
        raise KeyError(
            f"Missing read-error category: {key.value}"
        )

    values = error_report[key]

    if isinstance(values, (str, bytes)):
        raise TypeError(
            f"Read-error category {key.value!r} "
            "must contain a sequence of paths."
        )

    return [str(path) for path in values]


def _make_wrapped_path_table(
    paths: Sequence[str],
    styles,
) -> Table:
    """
    Build a one-column table in which long file paths can wrap.
    """
    path_style = ParagraphStyle(
        name="DatasetErrorPath",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        wordWrap="CJK",
    )

    header_style = ParagraphStyle(
        name="DatasetErrorPathHeader",
        parent=path_style,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )

    table_data = [
        [Paragraph("Source path", header_style)]
    ]

    table_data.extend(
        [
            [
                Paragraph(
                    escape(path),
                    path_style,
                )
            ]
            for path in paths
        ]
    )

    table = Table(
        table_data,
        colWidths=[25.0 * cm],
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def generate_binary_dataset_pdf_report(
    metadata: DatasetReportMetadata,
    split_report: Mapping[
        BinaryClassDatasetSplitStatistic,
        int,
    ],
    error_report: Mapping[
        BinaryClassDatasetReadError,
        Sequence[str],
    ],
    output_paths: Sequence[str | Path],
) -> None:
    """
    Generate identical PDF copies of a binary dataset split report.

    Parameters
    ----------
    metadata
        Dataset title, task description, labeling information, class
        definitions, and inclusion/exclusion criteria.

    split_report
        Patient counts and successfully saved image counts returned by
        split_datasets.

    error_report
        Source paths for images that could not be processed, grouped by
        split and class.

    output_paths
        Complete absolute paths for the PDF copies.

    Raises
    ------
    ValueError
        If metadata, statistics, or output paths are invalid.

    KeyError
        If a required statistic or error category is missing.

    FileExistsError
        If any requested output file already exists.

    Notes
    -----
    Existing files are never overwritten. If saving one copy fails,
    copies already created during the current call are removed.
    """
    paths = _validate_binary_dataset_report_paths(output_paths)
    _validate_dataset_report_metadata(metadata)

    split_definitions = (
        (
            "Training",
            BinaryClassDatasetSplitStatistic
            .TRAIN_NEGATIVE_PATIENT_NUM,
            BinaryClassDatasetSplitStatistic
            .TRAIN_POSITIVE_PATIENT_NUM,
            BinaryClassDatasetSplitStatistic
            .TRAIN_NEGATIVE_IMAGE_NUM,
            BinaryClassDatasetSplitStatistic
            .TRAIN_POSITIVE_IMAGE_NUM,
            BinaryClassDatasetReadError.TRAIN_NEGATIVE,
            BinaryClassDatasetReadError.TRAIN_POSITIVE,
        ),
        (
            "Validation",
            BinaryClassDatasetSplitStatistic
            .VALIDATION_NEGATIVE_PATIENT_NUM,
            BinaryClassDatasetSplitStatistic
            .VALIDATION_POSITIVE_PATIENT_NUM,
            BinaryClassDatasetSplitStatistic
            .VALIDATION_NEGATIVE_IMAGE_NUM,
            BinaryClassDatasetSplitStatistic
            .VALIDATION_POSITIVE_IMAGE_NUM,
            BinaryClassDatasetReadError.VALIDATION_NEGATIVE,
            BinaryClassDatasetReadError.VALIDATION_POSITIVE,
        ),
        (
            "Test",
            BinaryClassDatasetSplitStatistic
            .TEST_NEGATIVE_PATIENT_NUM,
            BinaryClassDatasetSplitStatistic
            .TEST_POSITIVE_PATIENT_NUM,
            BinaryClassDatasetSplitStatistic
            .TEST_NEGATIVE_IMAGE_NUM,
            BinaryClassDatasetSplitStatistic
            .TEST_POSITIVE_IMAGE_NUM,
            BinaryClassDatasetReadError.TEST_NEGATIVE,
            BinaryClassDatasetReadError.TEST_POSITIVE,
        ),
    )

    statistics_rows: list[dict[str, str | int]] = []
    error_rows: list[dict[str, str | int]] = []
    error_categories: list[
        tuple[str, str, list[str]]
    ] = []

    for (
        split_name,
        negative_patient_key,
        positive_patient_key,
        negative_image_key,
        positive_image_key,
        negative_error_key,
        positive_error_key,
    ) in split_definitions:
        statistics_rows.append(
            {
                "split": split_name,
                "negative_patients": _get_split_statistic(
                    split_report,
                    negative_patient_key,
                ),
                "positive_patients": _get_split_statistic(
                    split_report,
                    positive_patient_key,
                ),
                "negative_images": _get_split_statistic(
                    split_report,
                    negative_image_key,
                ),
                "positive_images": _get_split_statistic(
                    split_report,
                    positive_image_key,
                ),
            }
        )

        negative_errors = _get_dataset_error_paths(
            error_report,
            negative_error_key,
        )
        positive_errors = _get_dataset_error_paths(
            error_report,
            positive_error_key,
        )

        error_rows.extend(
            [
                {
                    "split": split_name,
                    "class": "Negative",
                    "failed_images": len(negative_errors),
                },
                {
                    "split": split_name,
                    "class": "Positive",
                    "failed_images": len(positive_errors),
                },
            ]
        )

        error_categories.extend(
            [
                (
                    split_name,
                    "Negative",
                    negative_errors,
                ),
                (
                    split_name,
                    "Positive",
                    positive_errors,
                ),
            ]
        )

    statistics_df = pd.DataFrame(statistics_rows)

    statistics_total = {
        "split": "Total",
        "negative_patients": int(
            statistics_df["negative_patients"].sum()
        ),
        "positive_patients": int(
            statistics_df["positive_patients"].sum()
        ),
        "negative_images": int(
            statistics_df["negative_images"].sum()
        ),
        "positive_images": int(
            statistics_df["positive_images"].sum()
        ),
    }

    statistics_df = pd.concat(
        [
            statistics_df,
            pd.DataFrame([statistics_total]),
        ],
        ignore_index=True,
    )

    errors_df = pd.DataFrame(error_rows)

    errors_df = pd.concat(
        [
            errors_df,
            pd.DataFrame(
                [
                    {
                        "split": "Total",
                        "class": "All classes",
                        "failed_images": int(
                            errors_df["failed_images"].sum()
                        ),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    negative_patient_total = int(
        statistics_df.iloc[:-1]["negative_patients"].sum()
    )
    positive_patient_total = int(
        statistics_df.iloc[:-1]["positive_patients"].sum()
    )
    negative_image_total = int(
        statistics_df.iloc[:-1]["negative_images"].sum()
    )
    positive_image_total = int(
        statistics_df.iloc[:-1]["positive_images"].sum()
    )

    negative_error_total = sum(
        len(error_paths)
        for _, class_name, error_paths in error_categories
        if class_name == "Negative"
    )
    positive_error_total = sum(
        len(error_paths)
        for _, class_name, error_paths in error_categories
        if class_name == "Positive"
    )

    patient_total = (
        negative_patient_total
        + positive_patient_total
    )
    saved_image_total = (
        negative_image_total
        + positive_image_total
    )
    error_total = (
        negative_error_total
        + positive_error_total
    )
    attempted_image_total = (
        saved_image_total
        + error_total
    )

    error_rate = (
        100.0 * error_total / attempted_image_total
        if attempted_image_total
        else 0.0
    )

    summary_df = pd.DataFrame(
        [
            {
                "metric": "Patients",
                "negative": negative_patient_total,
                "positive": positive_patient_total,
                "total": patient_total,
            },
            {
                "metric": "Successfully saved images",
                "negative": negative_image_total,
                "positive": positive_image_total,
                "total": saved_image_total,
            },
            {
                "metric": "Processing errors",
                "negative": negative_error_total,
                "positive": positive_error_total,
                "total": error_total,
            },
            {
                "metric": "Attempted images",
                "negative": (
                    negative_image_total
                    + negative_error_total
                ),
                "positive": (
                    positive_image_total
                    + positive_error_total
                ),
                "total": attempted_image_total,
            },
        ]
    )

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        name="DatasetReportBody",
        parent=styles["Normal"],
        alignment=TA_LEFT,
        fontSize=9,
        leading=13,
    )

    section_style = ParagraphStyle(
        name="DatasetReportSection",
        parent=styles["Heading2"],
        spaceBefore=0.35 * cm,
        spaceAfter=0.15 * cm,
    )

    story = [
        Paragraph(
            escape(metadata.title),
            styles["Title"],
        ),
        Spacer(1, 0.4 * cm),
        Paragraph(
            "Task Description",
            section_style,
        ),
        Paragraph(
            escape(metadata.task_description).replace(
                "\n",
                "<br/>",
            ),
            body_style,
        ),
        Paragraph(
            "Labeling",
            section_style,
        ),
        Paragraph(
            escape(metadata.labeling).replace(
                "\n",
                "<br/>",
            ),
            body_style,
        ),
        Paragraph(
            "Class Definitions",
            section_style,
        ),
    ]

    class_df = pd.DataFrame(
        [
            {
                "class": "Negative",
                "label": 0,
                "description": (
                    metadata.negative_class_description
                ),
            },
            {
                "class": "Positive",
                "label": 1,
                "description": (
                    metadata.positive_class_description
                ),
            },
        ]
    )

    story.append(
        _dataframe_to_reportlab_table(
            class_df,
            column_widths=[
                3.0 * cm,
                2.0 * cm,
                20.0 * cm,
            ],
        )
    )

    story.extend(
        [
            Paragraph(
                "Inclusion Criteria",
                section_style,
            ),
            Paragraph(
                escape(metadata.inclusion_criteria).replace(
                    "\n",
                    "<br/>",
                ),
                body_style,
            ),
            Paragraph(
                "Exclusion Criteria",
                section_style,
            ),
            Paragraph(
                escape(metadata.exclusion_criteria).replace(
                    "\n",
                    "<br/>",
                ),
                body_style,
            ),
            Paragraph(
                "Dataset Split Statistics",
                section_style,
            ),
            _dataframe_to_reportlab_table(
                statistics_df,
                column_widths=[
                    4.0 * cm,
                    5.0 * cm,
                    5.0 * cm,
                    5.0 * cm,
                    5.0 * cm,
                ],
            ),
            Paragraph(
                "Processing Errors",
                section_style,
            ),
            Paragraph(
                "Failed images are excluded from the successful "
                "image counts and from the generated CSV files.",
                body_style,
            ),
            _dataframe_to_reportlab_table(
                errors_df,
                column_widths=[
                    6.0 * cm,
                    6.0 * cm,
                    6.0 * cm,
                ],
            ),
        ]
    )

    if error_total == 0:
        story.extend(
            [
                Spacer(1, 0.15 * cm),
                Paragraph(
                    "No processing errors were recorded.",
                    body_style,
                ),
            ]
        )
    else:
        story.append(
            Paragraph(
                "Error Path Examples",
                section_style,
            )
        )

        for (
            split_name,
            class_name,
            error_paths,
        ) in error_categories:
            if not error_paths:
                continue

            displayed_paths = error_paths[
                :_BINARY_DATASET_ERROR_PATH_LIMIT
            ]

            story.extend(
                [
                    Paragraph(
                        (
                            f"{split_name} - {class_name} "
                            f"({len(error_paths)} failed images)"
                        ),
                        styles["Heading3"],
                    ),
                    _make_wrapped_path_table(
                        displayed_paths,
                        styles,
                    ),
                ]
            )

            omitted_count = (
                len(error_paths)
                - len(displayed_paths)
            )

            if omitted_count:
                story.append(
                    Paragraph(
                        (
                            f"{omitted_count} additional path(s) "
                            "are not shown in this PDF."
                        ),
                        body_style,
                    )
                )

    story.extend(
        [
            Paragraph(
                "Dataset Summary",
                section_style,
            ),
            _dataframe_to_reportlab_table(
                summary_df,
                column_widths=[
                    9.0 * cm,
                    5.0 * cm,
                    5.0 * cm,
                    5.0 * cm,
                ],
            ),
            Spacer(1, 0.15 * cm),
            Paragraph(
                (
                    "Overall processing error rate: "
                    f"{error_rate:.2f}%."
                ),
                body_style,
            ),
        ]
    )

    def draw_page_number(canvas, document) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(
            landscape(A4)[0] - 1.2 * cm,
            0.65 * cm,
            f"Page {document.page}",
        )
        canvas.restoreState()

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title=metadata.title,
        subject="Binary dataset split report",
        creator="Python ReportLab",
    )

    document.build(
        story,
        onFirstPage=draw_page_number,
        onLaterPages=draw_page_number,
    )

    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    for path in paths:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    written_paths: list[Path] = []

    try:
        for path in paths:
            with path.open("xb") as pdf_file:
                pdf_file.write(pdf_bytes)
                pdf_file.flush()
                os.fsync(pdf_file.fileno())

            written_paths.append(path)

    except BaseException:
        for written_path in reversed(written_paths):
            try:
                written_path.unlink(missing_ok=True)
            except OSError:
                pass

        raise