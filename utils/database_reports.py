from pathlib import Path

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

