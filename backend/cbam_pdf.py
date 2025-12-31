"""
PDF report generator for CBAM reports.

This module uses the FPDF library to create a simple, professional PDF
summary of the report data. It includes a title, reporting period and a
table listing the products with their emissions. The layout can be
customised further to match corporate branding and styling guidelines.
"""

from fpdf import FPDF
from typing import Any

from main import ReportRequest, Product  # type: ignore  # circular import resolved at runtime


def generate_pdf_report(report: ReportRequest, output_path: str) -> None:
    """Create a PDF report summarising the CBAM data.

    Args:
        report: Parsed request data containing the quarter and products.
        output_path: Path to write the PDF file.
    """
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "ISOTEC CBAM İletişim Raporu", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Dönem: {report.quarter}", ln=True, align="C")
    pdf.ln(5)

    # Table headers
    pdf.set_font("Arial", "B", 10)
    col_widths = [25, 60, 30, 30, 30, 30]  # define column widths
    headers = ["CN Kodu", "Ürün Tanımı", "Üretim (t)", "Direct SEE", "Indirect SEE", "Total SEE"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", size=9)
    for product in report.products:
        row_data = [
            product.cn_code,
            product.name,
            f"{product.production_ton:.2f}",
            f"{product.direct_see:.3f}",
            f"{product.indirect_see:.3f}",
            f"{product.total_see:.3f}",
        ]
        for i, cell_text in enumerate(row_data):
            # Align numbers to the right for better readability
            align = "R" if i > 1 else "L"
            pdf.cell(col_widths[i], 7, cell_text, border=1, align=align)
        pdf.ln()

    # Save the file
    pdf.output(output_path)