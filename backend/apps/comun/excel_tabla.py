"""Excel de cualquier tabla que la pantalla ya muestra (sin volver a consultar la base).

La pantalla envía la tabla tal como la dibuja: filas de encabezado (con celdas que
ocupan varias columnas o filas) y filas de datos. Aquí solo se arma el archivo con el
diseño de los reportes del sistema actual: título, encabezado azul, fila del total en
amarillo, filas alternadas y, al pie, FUENTE / FECHA Y HORA / SELECCIÓN.

Es lo mismo que hacía la pantalla actual con su "Exportar Excel" (copiaba la tabla del
navegador), pero genera un .xlsx real.
"""

from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from rest_framework import serializers

FUENTE = "Calibri"
_lado = Side(style="thin", color="BFBFBF")
BORDE = Border(left=_lado, right=_lado, top=_lado, bottom=_lado)
CENTRO = Alignment(horizontal="center", vertical="center", wrap_text=True)
IZQUIERDA = Alignment(horizontal="left", vertical="center")
MAX_CELDAS = 600_000


class CeldaEncabezadoSerializer(serializers.Serializer):
    texto = serializers.CharField(allow_blank=True, max_length=200)
    columnas = serializers.IntegerField(min_value=1, max_value=500, default=1)
    filas = serializers.IntegerField(min_value=1, max_value=10, default=1)


class FilaSerializer(serializers.Serializer):
    celdas = serializers.ListField(
        child=serializers.CharField(allow_blank=True, max_length=300), max_length=1000
    )
    total = serializers.BooleanField(default=False)
    # Índices de celdas a resaltar en rojo (mes del conglomerado)
    resaltadas = serializers.ListField(child=serializers.IntegerField(min_value=0), default=list)


class TablaExcelSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=300)
    nombre_archivo = serializers.RegexField(r"^[\w\- ]{1,120}$", default="reporte")
    color = serializers.RegexField(r"^[0-9A-Fa-f]{6}$", default="0065A9")
    encabezados = serializers.ListField(
        child=serializers.ListField(child=CeldaEncabezadoSerializer(), max_length=1000),
        max_length=10,
    )
    filas = serializers.ListField(child=FilaSerializer(), max_length=50_000)
    pie = serializers.ListField(
        child=serializers.CharField(max_length=500, allow_blank=True), max_length=5, default=list
    )

    def validate(self, datos):
        celdas = sum(len(f["celdas"]) for f in datos["filas"])
        if celdas > MAX_CELDAS:
            raise serializers.ValidationError("La tabla es demasiado grande para exportar.")
        return datos


def _texto(valor: str):
    if valor[:1] in ("=", "+", "@"):
        return "'" + valor
    return valor


def _valor(texto: str):
    """Números como números (para que Excel sume); códigos con ceros a la izquierda, texto."""
    t = texto.strip().replace(",", "")
    if t in ("", "-"):
        return texto.strip()
    if t.startswith("0") and len(t) > 1 and not t.startswith("0."):
        return t  # ODEI "08", conglomerado "001234", vivienda "001"
    try:
        n = float(t)
    except ValueError:
        return _texto(texto.strip())
    return int(n) if n.is_integer() and "." not in t else n


def libro(datos: dict) -> Workbook:
    color = PatternFill("solid", fgColor=datos["color"].upper())
    amarillo = PatternFill("solid", fgColor="F5FFBE")
    gris = PatternFill("solid", fgColor="EAEAEA")
    blanco = PatternFill("solid", fgColor="FFFFFF")

    wb = Workbook()
    hoja = wb.active
    hoja.title = "REPORTE"

    # Ancho total: el de la fila de encabezado más larga o de los datos
    ancho = max(
        [sum(c["columnas"] for c in fila) for fila in datos["encabezados"]]
        + [len(f["celdas"]) for f in datos["filas"]]
        + [1]
    )
    hoja.cell(2, 1, _texto(datos["titulo"])).font = Font(name=FUENTE, size=14, bold=True)
    hoja.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ancho)
    hoja.cell(2, 1).alignment = CENTRO
    hoja.row_dimensions[2].height = 24

    # Encabezados con celdas combinadas (respetando las que bajan desde filas anteriores)
    inicio = 3
    ocupadas: set[tuple[int, int]] = set()
    for i, fila in enumerate(datos["encabezados"]):
        r = inicio + i
        c = 1
        for celda in fila:
            while (r, c) in ocupadas:
                c += 1
            alto, cols = celda["filas"], celda["columnas"]
            for rr in range(r, r + alto):
                for cc in range(c, c + cols):
                    ocupadas.add((rr, cc))
                    x = hoja.cell(rr, cc)
                    x.fill, x.border, x.alignment = color, BORDE, CENTRO
                    x.font = Font(name=FUENTE, size=9, bold=True, color="FFFFFF")
            if alto > 1 or cols > 1:
                hoja.merge_cells(start_row=r, start_column=c, end_row=r + alto - 1,
                                 end_column=c + cols - 1)  # fmt: skip
            hoja.cell(r, c, _texto(celda["texto"]))
            c += cols

    r = inicio + len(datos["encabezados"])
    primera_datos = r
    for i, fila in enumerate(datos["filas"]):
        relleno = amarillo if fila["total"] else (gris if i % 2 else blanco)
        for c, texto in enumerate(fila["celdas"], start=1):
            x = hoja.cell(r, c, _valor(texto))
            x.fill, x.border = relleno, BORDE
            rojo = (c - 1) in fila["resaltadas"]
            x.font = Font(name=FUENTE, size=9, bold=fila["total"] or rojo,
                          color="FF2400" if rojo else "000000")  # fmt: skip
            x.alignment = IZQUIERDA if isinstance(x.value, str) and len(x.value) > 12 else CENTRO
        r += 1

    pie = Font(name=FUENTE, size=8, bold=True)
    hoja.cell(r, 1, "FUENTE: SISTEMA MONITOREO ENAHO").font = pie
    hoja.cell(
        r + 1, 1, f"FECHA Y HORA: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}"
    ).font = pie
    for k, linea in enumerate(datos["pie"], start=2):
        if linea:
            hoja.cell(r + k, 1, _texto(linea)).font = pie

    # Anchos según el contenido
    for c in range(1, ancho + 1):
        largo = max(
            (
                len(str(hoja.cell(f, c).value or ""))
                for f in range(primera_datos, min(r, primera_datos + 300))
            ),
            default=6,
        )
        hoja.column_dimensions[get_column_letter(c)].width = min(max(largo + 2, 7), 40)
    hoja.freeze_panes = hoja.cell(primera_datos, 3 if ancho > 3 else 1)
    hoja.page_setup.orientation = "landscape"
    hoja.page_setup.fitToWidth = 1
    hoja.page_setup.fitToHeight = 0
    hoja.sheet_properties.pageSetUpPr.fitToPage = True
    return wb


def respuesta(datos: dict) -> HttpResponse:
    contenido = BytesIO()
    libro(datos).save(contenido)
    r = HttpResponse(
        contenido.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    r["Content-Disposition"] = f'attachment; filename="{datos["nombre_archivo"]}.xlsx"'
    return r
