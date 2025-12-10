from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# =============================================================================
# 1. CARGA FLEXIBLE DE INVENTARIO
# =============================================================================
def load_inventory_excel(file):
    df = pd.read_excel(file)

    columnas = [
        "Código del Material",
        "Texto breve de material",
        "Unidad de medida base",
        "Ubicación",
        "Libre utilización",
    ]

    for c in columnas:
        if c not in df.columns:
            raise Exception(f"❌ Falta columna: {c}")

    df["Código del Material"] = df["Código del Material"].astype(str).str.strip()
    df["Ubicación"] = df["Ubicación"].astype(str).str.strip()

    return df


# =============================================================================
# ORDEN UBICACIONES
# =============================================================================
def sort_location_advanced(loc):
    try:
        if loc.startswith("E"):
            return int("".join([x for x in loc if x.isdigit()]))
        return 999999
    except:
        return 999999


# =============================================================================
#  GENERAR EXCEL SIN CORRUPCIÓN
# =============================================================================
def generate_discrepancies_excel(df):

    output = BytesIO()

    if df is None or df.empty:
        wb = Workbook()
        ws = wb.active
        ws.title = "Discrepancias"
        ws.append(["SIN DATOS"])
        wb.save(output)
        output.seek(0)
        return output

    df = df.astype(str)

    wb = Workbook()
    ws = wb.active
    ws.title = "Discrepancias"

    ws.append(list(df.columns))

    for _, row in df.iterrows():
        ws.append(row.tolist())

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E78")
    center = Alignment(horizontal="center")

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center

    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.border = border
            cell.alignment = center

    ws.auto_filter.ref = ws.dimensions

    wb.save(output)
    output.seek(0)
    return output
