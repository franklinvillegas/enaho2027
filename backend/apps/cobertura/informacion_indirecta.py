"""Tasa de información indirecta: las mismas vistas que la pantalla actual.

Pantalla actual: templates/.../indicadoresCobertura/infor_indirecta.html +
static/.../infor_indirecta.js. Procedimientos y orden de parámetros tomados de
consultasdb/api/views.py (sp_inforDirecta_t1, _t2, _t3, _t3_abs y
sp_informacionIndirecta_mapa).

Mismo esquema que la TNR total (usa el motor de tasas_no_respuesta.py). Diferencias:
  - columnas tii2026; en la vista por mes, con absolutos (enero_2026_abs)
  - filtro de encuestadores activos (sin exclusiones)
  - en la vista por mes el encabezado es "INFORMACIÓN INDIRECTA (VALORES PORCENTUALES)"
  - al entrar a una sede en la vista por mes, debajo va una segunda tabla con los
    valores absolutos por encuestador (enaho2015_calidad_ind01_31_abs)
"""

from . import tasas_no_respuesta as tnr
from .tasas_no_respuesta import Vista, mes, rango

INDICADOR = tnr.registrar(
    tnr.IndicadorTnr(
        codigo="informacion-indirecta",
        titulo="Tasa de información indirecta",
        titulo_pantalla="INFORMACIÓN INDIRECTA",
        titulo_excel="REPORTE INFORMACIÓN INDIRECTA",
        descripcion=(
            "La metodología de la ENAHO se caracteriza por la recolección de la información "
            "en forma directa de los residentes habituales del hogar de 14 años a más "
            "(variables de educación, salud, empleo y gastos del hogar). Sin embargo no siempre "
            "se logra entrevistar de forma directa, ante esta situación existe algunos casos "
            "excepcionales en los que el/la encuestador/a se ve obligado a recoger la "
            "información en forma indirecta a través de un informante calificado miembro del "
            "hogar."
        ),
        formula=(
            "TDI = N° residentes que omitieron el capítulo 500(empleo) / "
            "Total de residentes del hogar * 100"
        ),
        vistas={
            "departamentos": Vista(
                "Visualizar por Departamentos", "cobertura_tasaInformacionIndirecta_dep", rango
            ),
            "odei": Vista(
                "Visualizar por ODEI",
                "enaho2015_calidad_ind01_21",
                lambda f: [f["sede"], f["usuario"], *rango(f)],
            ),
            "odei-mes": Vista(
                "Visualizar por ODEI y por mes",
                "enaho2015_calidad_ind01_31",
                lambda f: [
                    f["sede"],
                    f["usuario"],
                    f["conglomerado"],
                    0,  # periodo: el combo está oculto en la pantalla actual, siempre 0
                    1 if f["solo_activos"] else 0,
                    f["periodo_inicio"],
                    f["periodo_fin"],
                    mes(f["mes_inicio"]),
                    mes(f["mes_fin"]),
                ],
            ),
        },
        absolutos=Vista(
            "INFORMACIÓN INDIRECTA {anio} (VALORES ABSOLUTOS)",
            "enaho2015_calidad_ind01_31_abs",
            lambda f: [f["sede"], 1 if f["solo_activos"] else 0, *rango(f)],
        ),
        procedimiento_mapa="enaho2015_inf_indirecta_map",
        prefijo="tii",
        filtros_extra=("solo_activos",),
        colorear_ultimo=True,
        titulo_meses="INFORMACIÓN INDIRECTA (VALORES PORCENTUALES)",
        titulo_detalle="INFORMACIÓN INDIRECTA (VALORES PORCENTUALES)",
        grafico={
            "titulo_barras": "INFORMACIÓN INDIRECTA",
            "eje_barras": "Tasa de Información indirecta %",
            "serie_barras": "Información indirecta",
            "color_barras": "#E0B7B7",
            "color_barra_ultima": "#B38B8B",
            "titulo_lineas": "INFORMACIÓN INDIRECTA",
            "eje_lineas": "Tasa de Información indirecta %",
            "etiqueta_mapa": "% información indirecta",
            "archivo": "RPT-INFORMACION-INDIRECTA",
        },
    )
)
