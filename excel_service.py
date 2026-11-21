import os
from datetime import datetime
from typing import Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "data", "exports")

def generate_excel_report(result_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generates a beautifully styled, enterprise-grade Excel (.xlsx) workbook
    for the tender analysis results.
    """
    if not output_path:
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in result_data.get("folder_name", "Tender") if c.isalnum() or c in (' ', '_', '-')).strip()
        filename = f"TenderAI_{safe_name}_{timestamp}.xlsx"
        output_path = os.path.join(EXPORTS_DIR, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tender Analysis Checklist"
    ws.views.sheetView[0].showGridLines = True

    # Color Palette Definitions
    PRIMARY_COLOR = "1E293B"      # Deep Slate/Navy
    ACCENT_COLOR = "2563EB"       # Royal Blue
    ACCENT_TEAL = "0D9488"        # Teal
    SUCCESS_BG = "ECFDF5"         # Soft Mint Green
    SUCCESS_TEXT = "065F46"       # Dark Emerald
    MUTED_BG = "F8FAFC"           # Soft Gray
    MUTED_TEXT = "64748B"         # Gray Text
    BORDER_COLOR = "CBD5E1"       # Light Slate Border

    # Fonts
    font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_sub = Font(name="Calibri", size=11, bold=False, color="E2E8F0")
    font_section = Font(name="Calibri", size=11, bold=True, color="1E293B")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_body = Font(name="Calibri", size=10, color="0F172A")
    font_dash = Font(name="Calibri", size=12, bold=True, color="94A3B8")
    font_badge_found = Font(name="Calibri", size=10, bold=True, color=SUCCESS_TEXT)
    font_badge_missing = Font(name="Calibri", size=10, bold=True, color="DC2626")

    # Fills
    fill_title = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    fill_kpi = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_found_row = PatternFill(start_color=SUCCESS_BG, end_color=SUCCESS_BG, fill_type="solid")
    fill_missing_row = PatternFill(start_color=MUTED_BG, end_color=MUTED_BG, fill_type="solid")

    # Borders
    thin_border_side = Side(border_style="thin", color=BORDER_COLOR)
    card_border = Border(top=thin_border_side, left=thin_border_side, right=thin_border_side, bottom=thin_border_side)

    # 1. Main Banner Header
    ws.merge_cells("A1:G2")
    cell_a1 = ws["A1"]
    cell_a1.value = f" AI TENDER AUDIT REPORT: {result_data.get('folder_name', 'Tender Project').upper()}"
    cell_a1.font = font_title
    cell_a1.fill = fill_title
    cell_a1.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    # 2. Executive Metadata & KPI Cards (Rows 4-6)
    folder_name = result_data.get("folder_name", "N/A")
    total_pts = result_data.get("total_points", 0)
    found_pts = result_data.get("found_points", 0)
    missing_pts = result_data.get("missing_points", 0)
    accuracy_score = result_data.get("accuracy_score", 0.0)
    created_at = result_data.get("created_at", datetime.now().isoformat())
    files_analyzed = ", ".join(result_data.get("files", [])) or "All Folder PDFs"

    # Meta Row 4
    ws["A4"] = "Tender Project:"
    ws["A4"].font = Font(name="Calibri", size=10, bold=True, color="475569")
    ws["B4"] = folder_name
    ws["B4"].font = Font(name="Calibri", size=10, bold=True, color="0F172A")

    ws["D4"] = "Audit Date:"
    ws["D4"].font = Font(name="Calibri", size=10, bold=True, color="475569")
    ws["E4"] = created_at[:19].replace("T", " ")
    ws["E4"].font = font_body

    ws["F4"] = "Total Checklist Points:"
    ws["F4"].font = Font(name="Calibri", size=10, bold=True, color="475569")
    ws["G4"] = total_pts
    ws["G4"].font = Font(name="Calibri", size=12, bold=True, color="1E3A8A")

    # Meta Row 5
    ws["A5"] = "Documents Analyzed:"
    ws["A5"].font = Font(name="Calibri", size=10, bold=True, color="475569")
    ws["B5"] = files_analyzed
    ws["B5"].font = font_body

    ws["D5"] = "Found / Answered:"
    ws["D5"].font = Font(name="Calibri", size=10, bold=True, color="475569")
    ws["E5"] = f"{found_pts} ({round(found_pts/max(1, total_pts)*100, 1)}%)"
    ws["E5"].font = Font(name="Calibri", size=11, bold=True, color="065F46")

    ws["F5"] = "Missing in Tender (-):"
    ws["F5"].font = Font(name="Calibri", size=10, bold=True, color="475569")
    ws["G5"] = f"{missing_pts} ({round(missing_pts/max(1, total_pts)*100, 1)}%)"
    ws["G5"].font = Font(name="Calibri", size=11, bold=True, color="991B1B")

    # Meta Row 6 - Accuracy Rating
    ws["A6"] = "AI Completeness / Accuracy Score:"
    ws["A6"].font = Font(name="Calibri", size=10, bold=True, color="1E293B")
    ws["B6"] = f"{accuracy_score}%"
    ws["B6"].font = Font(name="Calibri", size=13, bold=True, color="2563EB")

    # Style KPI table rows 4 to 6
    for r in range(4, 7):
        for c in range(1, 8):
            cell = ws.cell(row=r, column=c)
            cell.border = card_border

    # 3. Checklist Table Header (Row 8)
    headers = [
        "S.No",
        "Category",
        "Checklist Question / Criteria Point",
        "Extracted Answer / Value / Specification",
        "Status",
        "Source Document & Page / Clause Reference",
        "Confidence"
    ]
    header_row = 8
    for col_idx, text in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.value = text
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 5, 7] else "left", vertical="center", wrap_text=True)
        cell.border = card_border

    ws.row_dimensions[header_row].height = 28

    # 4. Data Rows
    results_list = result_data.get("results", [])
    current_row = 9

    for idx, item in enumerate(results_list, start=1):
        status = item.get("status", "Not Found")
        ans = str(item.get("answer", "-")).strip()
        is_found = (status == "Found" and ans != "-")

        # S.No
        c1 = ws.cell(row=current_row, column=1, value=idx)
        c1.alignment = Alignment(horizontal="center", vertical="top")

        # Category
        c2 = ws.cell(row=current_row, column=2, value=item.get("category", "General"))
        c2.alignment = Alignment(horizontal="left", vertical="top")

        # Question
        c3 = ws.cell(row=current_row, column=3, value=item.get("question", ""))
        c3.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # Answer
        c4 = ws.cell(row=current_row, column=4, value=ans)
        c4.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        if ans == "-":
            c4.font = font_dash
            c4.alignment = Alignment(horizontal="center", vertical="top")
        else:
            c4.font = font_body

        # Status
        c5 = ws.cell(row=current_row, column=5, value="Found" if is_found else "- Not Found")
        c5.alignment = Alignment(horizontal="center", vertical="top")
        c5.font = font_badge_found if is_found else font_badge_missing

        # Source Reference
        c6 = ws.cell(row=current_row, column=6, value=item.get("source", "-"))
        c6.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        if str(item.get("source", "-")).strip() == "-":
            c6.alignment = Alignment(horizontal="center", vertical="top")
            c6.font = font_dash

        # Confidence
        c7 = ws.cell(row=current_row, column=7, value=item.get("confidence", "-"))
        c7.alignment = Alignment(horizontal="center", vertical="top")

        # Apply row borders and styling
        for col in range(1, 8):
            cell = ws.cell(row=current_row, column=col)
            cell.border = card_border
            if not is_found and col not in [4, 6]:
                cell.fill = fill_missing_row

        current_row += 1

    # Column Widths Setup
    col_widths = {
        "A": 8,    # S.No
        "B": 22,   # Category
        "C": 42,   # Question
        "D": 48,   # Answer
        "E": 14,   # Status
        "F": 32,   # Source
        "G": 14    # Confidence
    }
    for col_letter, width in col_widths.items():
        ws.column_dimensions[col_letter].width = width

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    return output_path

class ExcelService:
    def generate_excel_report(self, result_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        return generate_excel_report(result_data, output_path=output_path)

excel_svc = ExcelService()
