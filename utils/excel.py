from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows


# =====================================================================
# 📌 1. CARGA FLEXIBLE DE INVENTARIO SISTEMA
# =====================================================================
def load_inventory_excel(file):
    """
    Lee un archivo Excel y valida que tenga todas las columnas obligatorias.
    """
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

    # Normalización
    df["Código del Material"] = df["Código del Material"].astype(str).str.strip()
    df["Ubicación"] = df["Ubicación"].astype(str).str.strip()

    return df



# =====================================================================
# 📌 2. ORDENAMIENTO AVANZADO DE UBICACIONES (E001B01, PLANTA etc.)
# =====================================================================
def sort_location_advanced(location):
    """
    Ordena ubicaciones tipo:
    - E006B01
    - E010A03
    - PLANTA, PATIO, etc.
    """
    try:
        if isinstance(location, str) and location.startswith("E"):
            num = "".join([c for c in location if c.isdigit()])
            return int(num)
        return 999999
    except:
        return 999999



# =====================================================================
# 📌 3. CARGA DEL EXCEL PARA MAPA 2D (FALTA EN TU SISTEMA)
# =====================================================================
def load_warehouse2d_excel(file):
    """
    Carga el Excel para el módulo ALMACÉN 2D.
    Valida columnas industriales estándar.
    """

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
            raise Exception(f"❌ Falta la columna obligatoria en mapa 2D: {col}")

    # Normalización
    df["Código del Material"] = df["Código del Material"].astype(str).str.strip()
    df["Ubicación"] = df["Ubicación"].astype(str).str.strip()

    return df



# =====================================================================
# 📌 4. GENERAR EXCEL PROFESIONAL DE DISCREPANCIAS
# =====================================================================
def generate_discrepancies_excel(df):
    """
    Genera un Excel profesional:
    - Encabezado azul
    - Colores GERDAU por estado
    - Autoajuste de columnas
    - Bordes
    - Filtros automáticos
    """

    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Discrepancias"

    # -------- DATAFRAME A EXCEL --------
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # -------- ESTILOS --------
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill("solid", fgColor="1F4E78")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Encabezados
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    # -------- AUTO WIDTH --------
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = max_len + 3

    # -------- COLORES POR ESTADO --------
    status_colors = {
        "OK": "C6EFCE",
        "FALTA": "FFEB9C",
        "CRÍTICO": "FFC7CE",
        "SOBRA": "BDD7EE",
    }

    estado_index = df.columns.get_loc("Estado")

    for row in ws.iter_rows(min_row=2):
        estado = row[estado_index].value
        color = status_colors.get(estado, None)

        for cell in row:
            cell.border = border
            cell.alignment = center

        if color:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor=color)

    # Filtros
    ws.auto_filter.ref = ws.dimensions

    wb.save(output)
    output.seek(0)
    return output
