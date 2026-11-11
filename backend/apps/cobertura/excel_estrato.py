"""Excel de la TNR según estrato, con el diseño de los reportes del sistema actual.

Cada pestaña de la pantalla (anual, por mes y por hogar) exporta su tabla con:
título, encabezado azul agrupado, fila del total en amarillo y, al pie,
"FUENTE: SISTEMA MONITOREO ENAHO - <título> - <detalle>" y la fecha.
Las columnas salen de los datos (años 2017..año actual), no están escritas a mano.
"""

import re
from datetime import date
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from . import tnr_estrato as est

AZUL = PatternFill("solid", fgColor="1565C0")
AMARILLO = PatternFill("solid", fgColor="F5FFBE")
GRIS = PatternFill("solid", fgColor="F2F2F2")
BLANCO = PatternFill("solid", fgColor="FFFFFF")
_lado = Side(style="thin", color="BFBFBF")
BORDE = Border(left=_lado, right=_lado, top=_lado, bottom=_lado)
CENTRO = Alignment(horizontal="center", vertical="center", wrap_text=True)
IZQUIERDA = Alignment(horizontal="left", vertical="center")
FUENTE = "Calibri"
MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
RE_ANIO = re.compile(r"^TNR(\d{4})$")


# ---------------------------------------------------------------------------------------
# Nombre de cada fila según el nivel (igual que la pantalla actual)
# ---------------------------------------------------------------------------------------


def es_area(fila) -> bool:
    return int(fila.get("ORDEN") or 0) in (0, 6, 12)


def nombre_fila_anual(f: dict, fila: dict) -> str:
    if f["tipo"] == 0:
        return fila.get("NOMBAREA") if es_area(fila) else est.ESTRATOS.get(int(fila["ESTRATO"]))
    if int(f["odei"]) == 0:
        return fila.get("NOMODEI")
    return fila.get("CONGLOME")


def nombre_fila_mensual(f: dict, fila: dict) -> str:
    if f["tipo"] == 0 or int(f["odei"]) == 0:
        return nombre_fila_anual(f, fila)
    if f["conglomerado"] == "0":
        return fila.get("CONGLOME")
    return fila.get("CONGLOME") if int(fila.get("ORDEN") or 0) == 0 else fila.get("VIVIENDA")


def titulo_nombre_anual(f: dict) -> str:
    if f["tipo"] == 0:
        return "ESTRATOS SOCIOECONOMICOS"
    return "ODEI" if int(f["odei"]) == 0 else "CONGLOMERADO"


# ---------------------------------------------------------------------------------------
# Escritura genérica: encabezados agrupados + filas
# ---------------------------------------------------------------------------------------


def _numero(valor, decimales=None):
    if valor is None or valor == "":
        return "-"
    try:
        n = float(valor)
    except TypeError, ValueError:
        texto = str(valor)
        return "'" + texto if texto[:1] in ("=", "+", "-", "@") else texto
    if decimales is not None:
        return round(n, decimales)
    return int(n) if n.is_integer() else n


def _libro(titulo, encabezados, filas_encabezado, filas, amarillas, negritas, detalle, anchos):
    """encabezados: [(fila, col, texto, filas_que_ocupa, columnas_que_ocupa)] desde la fila 1."""
    total_cols = len(anchos)
    libro = Workbook()
    hoja = libro.active
    hoja.title = "TNR SEGUN ESTRATO"

    hoja.cell(2, 1, titulo).font = Font(name=FUENTE, size=14, bold=True)
    hoja.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols)
    hoja.cell(2, 1).alignment = CENTRO
    hoja.row_dimensions[2].height = 24

    inicio = 3
    for fila, col, texto, alto, ancho in encabezados:
        f0 = inicio + fila - 1
        if alto > 1 or ancho > 1:
            hoja.merge_cells(start_row=f0, start_column=col, end_row=f0 + alto - 1,
                             end_column=col + ancho - 1)  # fmt: skip
        for r in range(f0, f0 + alto):
            for c in range(col, col + ancho):
                celda = hoja.cell(r, c)
                celda.fill, celda.border, celda.alignment = AZUL, BORDE, CENTRO
                celda.font = Font(name=FUENTE, size=9, bold=True, color="FFFFFF")
        hoja.cell(f0, col, texto)

    r = inicio + filas_encabezado
    for i, valores in enumerate(filas):
        relleno = AMARILLO if i in amarillas else (GRIS if i % 2 else BLANCO)
        for c, valor in enumerate(valores, start=1):
            celda = hoja.cell(r, c, valor)
            celda.fill, celda.border = relleno, BORDE
            celda.font = Font(name=FUENTE, size=9, bold=i in amarillas or i in negritas)
            celda.alignment = IZQUIERDA if c == 1 and isinstance(valor, str) else CENTRO
        r += 1
    if not filas:
        hoja.cell(r, 1, "Sin resultados para los filtros elegidos.").font = Font(
            name=FUENTE, size=9
        )
        r += 1

    pie = Font(name=FUENTE, size=8, bold=True)
    r += 1
    hoja.cell(
        r, 1, f"FUENTE: SISTEMA MONITOREO ENAHO - {titulo} - {detalle}".rstrip(" -")
    ).font = pie
    hoja.cell(r + 1, 1, f"FECHA: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}").font = pie

    for c, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(c)].width = ancho
    hoja.freeze_panes = hoja.cell(inicio + filas_encabezado, 2)
    hoja.page_setup.orientation = "landscape"
    hoja.page_setup.fitToWidth = 1
    hoja.page_setup.fitToHeight = 0
    hoja.sheet_properties.pageSetUpPr.fitToPage = True
    return libro


def _respuesta(libro, nombre) -> HttpResponse:
    contenido = BytesIO()
    libro.save(contenido)
    respuesta = HttpResponse(
        contenido.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}.xlsx"'
    return respuesta


# ---------------------------------------------------------------------------------------
# Las tres tablas
# ---------------------------------------------------------------------------------------

COLUMNAS_ANIO = ["TOTAL", "TOTAL_ABS", "PANEL", "PANEL_ABS", "NO PANEL", "NO PANEL_ABS"]


def anios_de(filas) -> list[int]:
    claves = {k for fila in filas for k in fila}
    return sorted(int(m.group(1)) for k in claves if (m := RE_ANIO.match(k)))


def valores_anio(fila, a) -> list:
    p_abs, np_abs = fila.get(f"TNR{a}P_ABS"), fila.get(f"TNR{a}NP_ABS")
    total_abs = None if p_abs is None and np_abs is None else (p_abs or 0) + (np_abs or 0)
    return [
        _numero(fila.get(f"TNR{a}"), 1), _numero(total_abs), _numero(fila.get(f"TNR{a}P"), 1),
        _numero(p_abs), _numero(fila.get(f"TNR{a}NP"), 1), _numero(np_abs),
    ]  # fmt: skip


def excel_anual(f, filas, detalle) -> HttpResponse:
    anios = anios_de(filas)
    encabezados = [(1, 1, titulo_nombre_anual(f), 2, 1)]
    for k, a in enumerate(anios):
        col = 2 + k * 6
        encabezados.append((1, col, a, 1, 6))
        encabezados += [(2, col + j, t, 1, 1) for j, t in enumerate(COLUMNAS_ANIO)]
    datos = [
        [nombre_fila_anual(f, fila), *[v for a in anios for v in valores_anio(fila, a)]]
        for fila in filas
    ]
    amarillas = {i for i, fila in enumerate(filas) if int(fila.get("ORDEN") or 0) == 0}
    negritas = {i for i, fila in enumerate(filas) if f["tipo"] == 0 and es_area(fila)}
    libro = _libro(est.TITULOS["anual"], encabezados, 2, datos, amarillas, negritas, detalle,
                   [30] + [9] * (6 * len(anios)))  # fmt: skip
    return _respuesta(libro, "TNR_segun_estrato_anual")


def excel_mensual(f, filas, detalle) -> HttpResponse:
    anio = date.today().year
    encabezados = [(1, 1, "ESTRATOS SOCIOECONOMICOS", 2, 1), (1, 2, f"TOTAL {anio}", 2, 1)]
    for k, nombre in enumerate(["PANEL", "NO PANEL"]):
        col = 3 + k * 26
        encabezados.append((1, col, nombre, 1, 26))
        titulos = [f"TOTAL {nombre}", "Abs"] + [t for m in MESES_CORTOS for t in (m, "Abs")]
        encabezados += [(2, col + j, t, 1, 1) for j, t in enumerate(titulos)]

    def fila_valores(fila):
        valores = [nombre_fila_mensual(f, fila), _numero(fila.get("TNR"), 1)]
        for g in ("P", "NP"):
            valores += [_numero(fila.get(f"TNR{g}"), 1), _numero(fila.get(f"TNR{g}_ABS"))]
            for m in range(1, 13):
                valores += [
                    _numero(fila.get(f"TNR{g}_{m}"), 1),
                    _numero(fila.get(f"TNR{g}_{m}_ABS")),
                ]
        return valores

    datos = [fila_valores(fila) for fila in filas]
    amarillas = {i for i, fila in enumerate(filas) if int(fila.get("ORDEN") or 0) == 0}
    negritas = {i for i, fila in enumerate(filas) if f["tipo"] == 0 and es_area(fila)}
    libro = _libro(est.TITULOS["mensual"], encabezados, 2, datos, amarillas, negritas, detalle,
                   [30, 10] + [7] * 52)  # fmt: skip
    return _respuesta(libro, "TNR_segun_estrato_mes")


COLUMNAS_HOGAR = [
    ("ID", "Nª"), ("ANIO", "Año"), ("ODEI", "ODEI"), ("NOMODEI", "Nombre ODEI"),
    ("DISTRITO", "Distrito"), ("NOMAREAGEN", "Area"), ("MES", "Mes"), ("PERIODO", "Periodo"),
    ("CONGLOME", "Conglomerado"), ("VIVIENDA", "Selección"), ("HOGAR", "Hogar"),
    ("RESULTADO", "Resultado"), ("TIPOVIVIENDA", "Tipo vivienda"), ("ESTRATO", "Estrato"),
    ("VIVIENDAS_CONGLOME", "Cant. Viviendas"), ("TNR_CONGLOME", "TNR"),
]  # fmt: skip


def excel_hogar(filas, detalle) -> HttpResponse:
    anio = date.today().year
    titulos = [t if c != "TNR_CONGLOME" else f"TNR {anio}" for c, t in COLUMNAS_HOGAR]
    encabezados = [(1, k + 1, t, 1, 1) for k, t in enumerate(titulos)]
    datos = [[_texto_o_numero(fila.get(c)) for c, _ in COLUMNAS_HOGAR] for fila in filas]
    libro = _libro(est.TITULOS["hogar"], encabezados, 1, datos, set(), set(), detalle,
                   [6, 7, 7, 22, 18, 10, 6, 8, 13, 10, 7, 10, 13, 8, 10, 9])  # fmt: skip
    return _respuesta(libro, "TNR_segun_estrato_hogar")


def _texto_o_numero(valor):
    # Códigos con ceros a la izquierda (ODEI, conglomerado, vivienda) se dejan como texto
    if isinstance(valor, str):
        return "'" + valor if valor[:1] in ("=", "+", "-", "@") else valor
    return _numero(valor)
