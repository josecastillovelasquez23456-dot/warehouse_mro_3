from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


# =====================================================================
# 1. CARGA FLEXIBLE DE INVENTARIO SISTEMA
# =====================================================================
def load_inventory_excel(file):
    df = pd.read_excel(file)

    columnas_requeridas = [
        "Código del Material",
        "Texto breve de material",
        "Unidad de medida base",
        "Ubicación",
        "Libre utilización"
    ]

    for col in columnas_requeridas:
        if col not in df.columns:
            raise Exception(f"❌ Falta la columna obligatoria: {col}")

    df["Código del Material"] = df["Código del Material"].astype(str).str.strip()
    df["Ubicación"] = df["Ubicación"].astype(str).str.strip()

    return df


# =====================================================================
# 2. ORDENAMIENTO AVANZADO DE UBICACIONES
# =====================================================================
def sort_location_advanced(location):
    try:
        if isinstance(location, str) and location.startswith("E"):
            nums = "".join([c for c in location if c.isdigit()])
            return int(nums)
        return 999999
    except:
        return 999999


# =====================================================================
# 3. MAPA 2D
# =====================================================================
def load_warehouse2d_excel(file):
    df = pd.read_excel(file)

    columnas_requeridas = [
        "Código del Material",
        "Texto breve de material",
        "Unidad de medida base",
        "Ubicación",
        "Stock máximo",
        "Consumo mes actual",
        "Libre utilización",
        "Tamaño de lote mínimo"
    ]

    for col in columnas_requeridas:
        if col not in df.columns:
            raise Exception(f"❌ Falta columna obligatoria en mapa 2D: {col}")

    df["Código del Material"] = df["Código del Material"].astype(str).str.strip()
    df["Ubicación"] = df["Ubicación"].astype(str).str.strip()

    return df


# =====================================================================
# 4. GENERAR EXCEL PROFESIONAL DE DISCREPANCIAS (FIX DEFINITIVO)
# =====================================================================
def generate_discrepancies_excel(df):
    """
    Genera un archivo Excel válido (sin corrupción),
    compatible con Windows + Railway.
    """

    output = BytesIO()

    # Si DF está vacío
    if df is None or df.empty:
        wb = Workbook()
        ws = wb.active
        ws.title = "Discrepancias"
        ws.append(["SIN DATOS"])
        wb.save(output)
        output.seek(0)
        return output

    # Normalizar todo a texto (evita corrupción)
    df = df.copy()
    df = df.astype(str)

    wb = Workbook()
    ws = wb.active
    ws.title = "Discrepancias"

    # Cabeceras
    ws.append(list(df.columns))

    # Filas
    for _, row in df.iterrows():
        ws.append(row.tolist())

    # Estilos
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E78")
    center = Alignment(horizontal="center", vertical="center")

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

    # Colores por estado
    status_colors = {
        "OK": "C6EFCE",
        "FALTA": "FFEB9C",
        "CRÍTICO": "FFC7CE",
        "SOBRA": "BDD7EE",
    }

    if "Estado" in df.columns:
        idx = list(df.columns).index("Estado") + 1

        for row in ws.iter_rows(min_row=2):
            estado = row[idx - 1].value
            color = status_colors.get(estado)
            if color:
                for cell in row:
                    cell.fill = PatternFill("solid", fgColor=color)

    # Auto-ancho
    for col in ws.columns:
        max_len = max(len(str(c.value)) for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 3

    ws.auto_filter.ref = ws.dimensions

    wb.save(output)
    output.seek(0)

    return output
