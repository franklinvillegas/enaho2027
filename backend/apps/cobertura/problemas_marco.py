"""Tasa de problemas de marco: las mismas vistas que la pantalla actual.

Pantalla actual: templates/.../indicadoresCobertura/tasa_problemaMarco.html +
static/.../tasa_problemaMarco.js. Procedimientos y orden de parámetros tomados de
consultasdb/api/views.py (sp_tasa_prob_marco_t1, sp_tasa_prob_marco_t2567 y
sp_tasa_prob_marco_mapa_calor).

Mismo esquema que la TNR (tres vistas, profundización nacional > sede > encuestador >
conglomerado), por eso usa el motor de tasas_no_respuesta.py. Diferencias:
  - columnas por año tpm_2026, sin absolutos; por mes enero_2026 ... sin absolutos
  - sin filtros de exclusiones ni de encuestadores activos
  - barras verdes, la del año en curso más oscura; escala azul en el último año
"""

from . import tasas_no_respuesta as tnr
from .tasas_no_respuesta import Vista, rango

INDICADOR = tnr.registrar(
    tnr.IndicadorTnr(
        codigo="problemas-marco",
        titulo="Tasa de problemas de marco",
        titulo_excel="TASA DE PROBLEMAS DE MARCO",
        descripcion=(
            "La Tasa de Problemas de Marco es el resultado del número de viviendas con "
            "resultado: desocupada, no se inició la entrevista y otros, entre el total de "
            "viviendas programadas."
        ),
        formula="Tasa Prob. Marco = Viv. con resultado (result 5,6,7) / Total Viv. Prog. * 100",
        vistas={
            "departamentos": Vista(
                "Visualizar por Departamentos", "cobertura_tasaProblemasMarco_dep", rango
            ),
            "odei": Vista(
                "Visualizar por ODEI",
                "enaho2015_cobertura_ind02_2",
                lambda f: [f["sede"], f["usuario"], *rango(f)],
            ),
            "odei-mes": Vista(
                "Visualizar por ODEI y por mes",
                "enaho2015_cobertura_ind02_3",
                lambda f: [f["sede"], f["usuario"], f["conglomerado"], *rango(f)],
            ),
        },
        procedimiento_mapa="enaho2015_tpm_map",
        prefijo="tpm_",
        colorear_ultimo=True,
        titulo_detalle="TASA PROBLEMAS DE MARCO (VALORES PORCENTUALES)",
        grafico={
            "titulo_barras": "Tasa de problemas de marco",
            "eje_barras": "Tasa de problemas de marco %",
            "serie_barras": "Tasa de problemas de marco",
            "color_barras": "#D8E1BF",
            "color_barra_ultima": "#89A590",
            "titulo_lineas": "Tasa de problemas de marco",
            "eje_lineas": "Tasa de problemas de marco %",
            "etiqueta_mapa": "% problemas de marco",
            "archivo": "TASA-PROBLEMAS-MARCO",
        },
    )
)
