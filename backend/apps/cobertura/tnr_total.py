"""Tasa de no respuesta total: las mismas vistas que la pantalla actual.

Pantalla actual: templates/.../tasaNoRespuesta/tnr_total.html + static/.../tnr_total.js.
Cada botón de la pantalla es una VISTA con su procedimiento. La profundización
(nacional > sede > encuestador > conglomerado) se hace dentro de la vista, llamando al
mismo procedimiento con sede, usuario y conglomerado distintos ("0" = todos).
El motor común está en tasas_no_respuesta.py.
"""

from . import tasas_no_respuesta as tnr
from .tasas_no_respuesta import MESES, Vista, mes, rango

INDICADOR = tnr.registrar(
    tnr.IndicadorTnr(
        codigo="tnr-total",
        titulo="Tasa de no respuesta total",
        titulo_excel="TNR TOTAL",
        descripcion=(
            "La Tasa de No Respuesta Total, se define como la proporción de viviendas ocupadas "
            "cuyos informantes no desean ser entrevistados (rechazo) o no están presentes en "
            "el momento de la entrevista. Por lo tanto, este indicador mide la proporción de "
            "hogares que no se entrevistaron entre el total de viviendas ocupadas."
        ),
        formula=(
            "TNR (Neta) = Viv. Resultado 3 y 4 (rechazo y ausente) / "
            "Viv. Resultado 1, 2, 3 y 4 (ocupadas) * 100"
        ),
        vistas={
            "departamentos": Vista(
                "Visualizar por Departamentos", "cobertura_tasaNoRespuestaTotal_dep", rango
            ),
            "odei": Vista(
                "Visualizar por ODEI",
                "enaho2015_cobertura_ind03_2_v2",
                lambda f: [f["sede"], f["usuario"], *rango(f)],
            ),
            "odei-mes": Vista(
                "Visualizar por ODEI y por mes",
                "enaho2015_cobertura_ind03_3_v4",
                lambda f: [
                    f["sede"],
                    f["usuario"],
                    f["conglomerado"],
                    f["periodo_inicio"],
                    f["periodo_fin"],
                    1 if f["solo_activos"] else 0,
                    mes(f["mes_inicio"]),
                    mes(f["mes_fin"]),
                    f["excluir"],
                ],
            ),
        },
        procedimiento_mapa="enaho2015_tnr_total_map",
        prefijo="tnr",
        filtros_extra=("excluir", "solo_activos"),
        colorear_ultimo=True,
        titulo_detalle="TNR TOTAL",
        grafico={
            "titulo_barras": "% Tasa de No Respuesta Total",
            "eje_barras": "% TNR Total",
            "serie_barras": "TNR_Total",
            "color_barras": "#DDB4B4",
            "color_barra_ultima": "#DDB4B4",
            "titulo_lineas": "Tasa de No Respuesta Total",
            "eje_lineas": "% Tasa de no Respuesta",
            "etiqueta_mapa": "% TNR total",
        },
    )
)

# Nombres usados por las vistas y las pruebas
TITULO = INDICADOR.titulo
DESCRIPCION = INDICADOR.descripcion
FORMULA = INDICADOR.formula
VISTAS = INDICADOR.vistas
PROCEDIMIENTO_MAPA = INDICADOR.procedimiento_mapa
FiltrosTnrTotalSerializer = tnr.FiltrosTnrSerializer
verificar_alcance = tnr.verificar_alcance


def consultar(vista: str, filtros: dict) -> list[dict]:
    return tnr.consultar(INDICADOR, vista, filtros)


def consultar_mapa() -> list[dict]:
    return tnr.consultar_mapa(INDICADOR)


def etiqueta_columna(columna: str) -> str:
    """Encabezado legible: tnr2026 -> 2026, enero_2026_abs -> Ene 2026 (abs)."""
    fijas = {"idmostrar": "N°", "nombremostrar": "Nombre", "tipenc": "Tipo de encuesta",
             "viv": "Viviendas trabajadas"}  # fmt: skip
    c = columna.lower()
    if c in fijas:
        return fijas[c]
    abs_ = c.endswith("_abs")
    base = c.removesuffix("_abs")
    if base.startswith("tnr") and base.removeprefix("tnrp_").removeprefix("tnr").isdigit():
        texto = base.removeprefix("tnrp_").removeprefix("tnr")
    elif "_" in base and base.split("_")[0] in MESES:
        nombre, anio = base.split("_", 1)
        texto = f"{nombre[:3].capitalize()} {anio}"
    else:
        texto = columna.replace("_", " ").capitalize()
    return f"{texto} (abs)" if abs_ else texto
