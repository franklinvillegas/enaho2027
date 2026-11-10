"""Exportación a Excel hecha en el servidor (antes se armaba en el navegador)."""

from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def respuesta_excel(
    nombre_archivo: str,
    titulo: str,
    columnas: list[str],
    filas: list[dict],
    etiquetas: dict | None = None,
):
    libro = Workbook()
    hoja = libro.active
    hoja.title = titulo[:31]
    hoja.append([(etiquetas or {}).get(c, c) for c in columnas])
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    for fila in filas:
        hoja.append([fila.get(c) for c in columnas])
    for i, columna in enumerate(columnas, start=1):
        hoja.column_dimensions[get_column_letter(i)].width = max(12, len(str(columna)) + 2)
    hoja.freeze_panes = "A2"

    contenido = BytesIO()
    libro.save(contenido)
    respuesta = HttpResponse(
        contenido.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.xlsx"'
    return respuesta
