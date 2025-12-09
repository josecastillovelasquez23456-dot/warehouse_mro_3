from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows


def generate_discrepancies_excel(df):
    output = BytesIO()

    # Crear libro
    wb = Workbook()
    ws = wb.active
    ws.title = "Discrepancias"

    # Agregar DataFrame al Excel
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # ======== ESTILOS =========
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill("solid", fgColor="1F4E78")  # Azul industrial GERDAU
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Aplicar estilos a encabezados
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    # ======== ANCHO AUTOMÁTICO =========
    for col in ws.columns:
        max_len = 0
        column = col[0].column_letter
        for cell in col:
            try:
                cell_len = len(str(cell.value))
                max_len = max(max_len, cell_len)
            except:
                pass
        ws.column_dimensions[column].width = max_len + 3

    # ======== COLORES POR ESTADO =========
    status_colors = {
        "OK": "C6EFCE",        # VERDE
        "FALTA": "FFEB9C",     # AMARILLO
        "CRÍTICO": "FFC7CE",   # ROJO
        "SOBRA": "BDD7EE",     # AZUL
    }

    estado_col = None
    for cell in ws[1]:
        if cell.value == "Estado":
            estado_col = cell.column_letter
            break

    if estado_col:
        for row in ws.iter_rows(min_row=2):
            estado = row[ df.columns.get_loc("Estado") ].value
            fill_color = status_colors.get(estado, None)

            for cell in row:
                cell.alignment = center
                cell.border = border

            if fill_color:
                for cell in row:
                    cell.fill = PatternFill("solid", fgColor=fill_color)

    # Filtros automáticos
    ws.auto_filter.ref = ws.dimensions

    wb.save(output)
    output.seek(0)
    return output
