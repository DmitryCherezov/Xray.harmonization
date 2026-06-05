from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
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
        
    doc.build(story)

    print(f"PDF report saved to: {output_pdf_path}")


