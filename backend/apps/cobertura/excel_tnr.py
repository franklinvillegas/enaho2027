"""Excel de las tasas de no respuesta con el mismo diseño del reporte del sistema actual.

Estructura (igual a la tabla de la pantalla):
    fila 2  : título "TNR TOTAL NACIONAL" / "TNR PARCIAL NACIONAL" (o la sede / encuestador)
    fila 3  : N° | <nombre> | AÑOS ...................................
    fila 4  :    |          | 2025 ........ | 2026 ........   (solo vista por mes)
    fila 5  :    |          | Total Abs Ene Abs ...           (o un año por columna)
    datos   : primera fila y títulos de sección en amarillo; el resto alternado en gris
    al final: FUENTE y FECHA Y HORA
Las columnas se arman con los datos, igual que en la pantalla (composables/tablaTnr.js).
"""

import re
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .tasas_no_respuesta import MESES, IndicadorTnr

MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
RE_MES = re.compile(rf"^({'|'.join(MESES)})_(\d{{4}})$", re.IGNORECASE)

AZUL = PatternFill("solid", fgColor="0065A9")
AMARILLO = PatternFill("solid", fgColor="F5FFBE")
GRIS = PatternFill("solid", fgColor="EAEAEA")
BLANCO = PatternFill("solid", fgColor="FFFFFF")
_lado = Side(style="thin", color="000000")
BORDE = Border(left=_lado, right=_lado, top=_lado, bottom=_lado)
CENTRO = Alignment(horizontal="center", vertical="center", wrap_text=True)
IZQUIERDA = Alignment(horizontal="left", vertical="center")
FUENTE = "Calibri"


def _escala_azul(valor):
    """Escala de la última columna (colorCasilla, caso 6, del sistema actual)."""
    try:
        v = float(valor)
    except TypeError, ValueError:
        return None, None
    escala = [(33.33, "DCF2FD", "000000"), (66.66, "ACD6F2", "FFFFFF"),
              (89.99, "4DBEED", "FFFFFF"), (99.99, "00A5E8", "FFFFFF")]  # fmt: skip
    for tope, fondo, texto in escala:
        if v <= tope:
            return fondo, texto
    return "007DC5", "FFFFFF"


def modelo_columnas(
    columnas: list[str], prefijo: str = "tnr", colorear_ultimo: bool = True
) -> tuple[str, list[dict]]:
    """Devuelve ("meses" | "anios", grupos).

    Cada grupo: {"anio", "columnas": [(clave, titulo, colorear), ...]}.
    prefijo: "tnr" (tnr2026) o "tnrp_" (tnrp_2026). Si cada año trae su absoluto
    (tnrp_2026_abs) se agrega la columna "Abs." al lado, como en la TNR parcial.
    """
    re_anio = re.compile(rf"^{re.escape(prefijo)}(\d{{4}})$", re.IGNORECASE)
    anios_mes = sorted({int(m.group(2)) for c in columnas if (m := RE_MES.match(c))})
    if anios_mes:
        grupos = []
        for anio in anios_mes:
            cols = []
            if f"{prefijo}{anio}" in columnas:
                cols += [
                    (f"{prefijo}{anio}", "Total", False),
                    (f"{prefijo}{anio}_abs", "Abs", False),
                ]
            for mes, corto in zip(MESES, MESES_CORTOS, strict=True):
                cols += [(f"{mes}_{anio}", corto, False), (f"{mes}_{anio}_abs", "Abs", False)]
            grupos.append({"anio": anio, "columnas": [c for c in cols if c[0] in columnas]})
        return "meses", grupos
    anios = sorted(int(m.group(1)) for c in columnas if (m := re_anio.match(c)))
    cols = []
    for i, a in enumerate(anios):
        cols.append((f"{prefijo}{a}", str(a), colorear_ultimo and i == len(anios) - 1))
        if f"{prefijo}{a}_abs" in columnas:
            cols.append((f"{prefijo}{a}_abs", "Abs.", False))
    return "anios", [{"anio": None, "columnas": cols}]


def nivel_de(filtros: dict) -> int:
    if filtros["sede"] == "0":
        return 1
    if filtros["usuario"] == "0":
        return 2
    return 3 if filtros["conglomerado"] == "0" else 4


def _columnas_fijas(vista: str, nivel: int, columnas: list[str]):
    if nivel == 1:
        nombre = ("nombreMostrar", "DOMINIOS DE ESTUDIO" if vista == "departamentos" else "ODEI")
    elif nivel == 2:
        nombre = ("encuestador", "ENCUESTADOR")
    else:
        nombre = ("conglomerado", "CONGLOMERADO")
    # Detalle de un conglomerado: N° | MES | CONGLOMERADO | VIVIENDA | HOGAR | valores
    izq = [("mes", "MES")] if nivel == 4 else []
    tras = [("vivienda", "VIVIENDA"), ("hogar", "HOGAR")] if nivel == 4 else []
    der = [("tipEnc", "TIPO DE ENCUESTA"), ("viv", "VIVIENDAS TRABAJADAS")] if nivel == 3 else []
    return (
        [c for c in izq if c[0] in columnas],
        nombre,
        [c for c in tras if c[0] in columnas],
        [c for c in der if c[0] in columnas],
    )


def _texto(valor):
    """Evita que un texto que empieza con = + - @ se lea como fórmula en Excel."""
    if isinstance(valor, str) and valor[:1] in ("=", "+", "-", "@"):
        return "'" + valor
    return valor


def _numero(valor):
    if valor is None or valor == "":
        return "-"
    try:
        n = float(valor)
    except TypeError, ValueError:
        return _texto(str(valor))
    return int(n) if n.is_integer() else round(n, 1)


def _id(fila: dict):
    """N° de la fila: idMostrar en el primer nivel, id en los siguientes."""
    return fila.get("idMostrar", fila.get("id"))


def libro_tnr(
    indicador: IndicadorTnr, vista: str, filtros: dict, filas: list[dict], ambito: str
) -> Workbook:
    # Todas las columnas que trae alguna fila (la del total a veces no trae mes, vivienda...)
    columnas = list(dict.fromkeys(k for fila in filas for k in fila))
    nivel = nivel_de(filtros)
    tipo, grupos = modelo_columnas(columnas, indicador.prefijo, indicador.colorear_ultimo)
    izq, (clave_nombre, titulo_nombre), tras, der = _columnas_fijas(vista, nivel, columnas)
    datos = [c for g in grupos for c in g["columnas"]]

    libro = Workbook()
    hoja = libro.active
    hoja.title = indicador.titulo_excel
    hoja.sheet_view.showGridLines = True

    # Columnas: N°, extras izquierda, nombre, datos, extras derecha
    fijas_izq = [("idMostrar", "N°"), *izq, (clave_nombre, titulo_nombre), *tras]
    col_nombre = 2 + len(izq)
    total_columnas = len(fijas_izq) + len(datos) + len(der)
    filas_encabezado = 3 if tipo == "meses" else 2
    primera = 3
    ultima_enc = primera + filas_encabezado - 1

    # Título
    hoja.cell(2, 1, f"{indicador.titulo_excel} {ambito or 'NACIONAL'}")
    hoja.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max(total_columnas, 1))
    hoja.cell(2, 1).font = Font(name=FUENTE, size=14, bold=True)
    hoja.cell(2, 1).alignment = CENTRO

    def encabezado(fila, col, texto, hasta_fila=None, hasta_col=None):
        hasta_fila, hasta_col = hasta_fila or fila, hasta_col or col
        if (hasta_fila, hasta_col) != (fila, col):
            hoja.merge_cells(
                start_row=fila, start_column=col, end_row=hasta_fila, end_column=hasta_col
            )
        for f in range(fila, hasta_fila + 1):
            for c in range(col, hasta_col + 1):
                celda = hoja.cell(f, c)
                celda.fill, celda.border, celda.alignment = AZUL, BORDE, CENTRO
                celda.font = Font(name=FUENTE, size=9, bold=True, color="FFFFFF")
        hoja.cell(fila, col, texto)

    col = 1
    for _, titulo in fijas_izq:
        encabezado(primera, col, titulo, hasta_fila=ultima_enc)
        col += 1
    inicio_datos = col
    if datos:
        titulo_anios = indicador.titulo_detalle if nivel == 4 else "AÑOS"
        encabezado(primera, col, titulo_anios, hasta_col=col + len(datos) - 1)
        for g in grupos:
            if tipo == "meses":
                encabezado(primera + 1, col, g["anio"], hasta_col=col + len(g["columnas"]) - 1)
            for _, titulo, _ in g["columnas"]:
                encabezado(ultima_enc, col, titulo)
                col += 1
    for _, titulo in der:
        encabezado(primera, col, titulo, hasta_fila=ultima_enc)
        col += 1

    # Datos
    f = ultima_enc + 1
    for i, fila in enumerate(filas):
        es_total = i == 0 or str(_id(fila)) == "0"
        seccion = i != 0 and str(_id(fila)) == "0"
        relleno = AMARILLO if es_total else (GRIS if i % 2 else BLANCO)
        nombre = fila.get(clave_nombre)
        if nombre in (None, ""):
            nombre = fila.get("nombreMostrar")
        valores = [
            "" if es_total else _numero(_id(fila)),
            *[_texto(fila.get(c)) for c, _ in izq],
            _texto(nombre),
            *[_texto(fila.get(c)) for c, _ in tras],
            *["-" if seccion else _numero(fila.get(c)) for c, _, _ in datos],
            *[_texto(fila.get(c)) for c, _ in der],
        ]
        for c, valor in enumerate(valores, start=1):
            celda = hoja.cell(f, c, valor)
            celda.fill, celda.border = relleno, BORDE
            celda.font = Font(name=FUENTE, size=9, bold=es_total)
            celda.alignment = IZQUIERDA if c == col_nombre else CENTRO
        # Escala azul en la última columna de años (vistas por año)
        for k, (clave, _, colorear) in enumerate(datos):
            if colorear and not seccion:
                fondo, texto = _escala_azul(fila.get(clave))
                if fondo:
                    celda = hoja.cell(f, inicio_datos + k)
                    celda.fill = PatternFill("solid", fgColor=fondo)
                    celda.font = Font(name=FUENTE, size=9, bold=es_total, color=texto)
        f += 1

    if not filas:
        aviso = hoja.cell(f, 1, "Sin resultados para los filtros elegidos.")
        aviso.font = Font(name=FUENTE, size=9)
        f += 1

    # Pie
    pie = Font(name=FUENTE, size=8, bold=True)
    hoja.cell(f, 1, "FUENTE: SISTEMA MONITOREO ENAHO").font = pie
    ahora = timezone.localtime().strftime("%d/%m/%Y %H:%M")
    hoja.cell(f + 1, 1, f"FECHA Y HORA: {ahora}").font = pie

    # Anchos, alto del título, paneles fijos e impresión
    for c in range(1, total_columnas + 1):
        letra = get_column_letter(c)
        if c == col_nombre:
            hoja.column_dimensions[letra].width = 26
        elif c == 1:
            hoja.column_dimensions[letra].width = 6
        elif c < inicio_datos or c >= inicio_datos + len(datos):
            hoja.column_dimensions[letra].width = 14
        else:
            hoja.column_dimensions[letra].width = 6.5 if tipo == "meses" else 8
    hoja.row_dimensions[2].height = 24
    hoja.freeze_panes = hoja.cell(ultima_enc + 1, inicio_datos)
    hoja.page_setup.orientation = "landscape"
    hoja.page_setup.fitToWidth = 1
    hoja.page_setup.fitToHeight = 0
    hoja.sheet_properties.pageSetUpPr.fitToPage = True
    return libro


def respuesta_tnr(
    indicador: IndicadorTnr, vista: str, filtros: dict, filas: list[dict], ambito: str
) -> HttpResponse:
    contenido = BytesIO()
    libro_tnr(indicador, vista, filtros, filas, ambito).save(contenido)
    respuesta = HttpResponse(
        contenido.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="{indicador.codigo}_{vista}.xlsx"'
    return respuesta
