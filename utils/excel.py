from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows


# =====================================================================
# 📌 1. CARGA FLEXIBLE DE INVENTARIO SISTEMA
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
# 📌 2. ORDENAMIENTO AVANZADO DE UBICACIONES
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
# 📌 3. CARGA DEL EXCEL PARA MAPA 2D
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
# 📌 4. GENERAR EXCEL PROFESIONAL DE DISCREPANCIAS (VERSION FIJA)
# =====================================================================
def generate_discrepancies_excel(df):
    output = BytesIO()

    # VALIDACIÓN: si llega vacío, crear un Excel válido para evitar corrupción
    if df is None or df.empty:
        wb = Workbook()
        ws = wb.active
        ws.title = "Discrepancias"
        ws.append(["SIN DATOS", "El DataFrame llegó vacío"])
        wb.save(output)
        output.seek(0)
        return output

    # Normalización fuerte para evitar corrupción
    df = df.copy()
    for col in df.columns:
        if "Material" in col or "Ubicación" in col:
            df[col] = df[col].astype(str)

    df["Stock sistema"] = pd.to_numeric(df["Stock sistema"], errors="coerce").fillna(0)
    df["Stock contado"] = pd.to_numeric(df["Stock contado"], errors="coerce").fillna(0)
    df["Diferencia"] = pd.to_numeric(df["Diferencia"], errors="coerce").fillna(0)

    wb = Workbook()
    ws = wb.active
    ws.title = "Discrepancias"

    # DataFrame a Excel
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # Estilos
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill("solid", fgColor="1F4E78")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Encabezados
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    # Auto ancho
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = max_len + 3

    # Colores según estado
    colors = {
        "OK": "C6EFCE",
        "FALTA": "FFEB9C",
        "CRÍTICO": "FFC7CE",
        "SOBRA": "BDD7EE",
    }

    estado_index = df.columns.get_loc("Estado")

    for row in ws.iter_rows(min_row=2):
        estado = row[estado_index].value
        color = colors.get(estado)

        for cell in row:
            cell.border = border
            cell.alignment = center

        if color:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor=color)

    ws.auto_filter.ref = ws.dimensions

    wb.save(output)
    output.seek(0)
    return output
