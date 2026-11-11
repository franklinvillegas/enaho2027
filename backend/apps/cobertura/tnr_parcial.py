"""Tasa de no respuesta parcial: las mismas vistas que la pantalla actual.

Pantalla actual: templates/.../tasaNoRespuesta/tnr_parcial.html + static/.../tnr_parcial.js.
Procedimientos y orden de parámetros tomados de consultasdb/api/views.py
(sp_tnrParcial_t1, sp_tnrParcial_t23 y sp_tnrParcial_mapa).

Diferencias con la TNR total:
  - columnas por año con guion bajo y con absoluto: tnrp_2026, tnrp_2026_abs
  - sin filtros de exclusiones ni de encuestadores activos
  - la vista por ODEI y mes recibe un "periodo" fijo en 0 (así lo manda la pantalla actual)
"""

from . import tasas_no_respuesta as tnr
from .tasas_no_respuesta import Vista, mes, rango

INDICADOR = tnr.registrar(
    tnr.IndicadorTnr(
        codigo="tnr-parcial",
        titulo="Tasa de no respuesta parcial",
        titulo_excel="TNR PARCIAL",
        descripcion=(
            "La Tasa de No Respuesta Parcial, proviene de la omisión de alguno de los miembros "
            "del hogar a los capítulos de educación, salud o empleo, es decir si alguno de los "
            "miembros del hogar no respondió a alguno de los capítulos 300(educación), "
            "400(salud) o 500(empleo), se considera hogar con no respuesta parcial."
        ),
        formula=(
            "TNR Parcial = Total de Hogares con No Respuesta Parcial / Total de Hogares * 100"
        ),
        vistas={
            "departamentos": Vista(
                "Visualizar por Departamentos", "cobertura_tasaNoRespuestaParcial_dep", rango
            ),
            "odei": Vista(
                "Visualizar por ODEI",
                "enaho2015_cobertura_ind04_2",
                lambda f: [f["sede"], f["usuario"], *rango(f)],
            ),
            "odei-mes": Vista(
                "Visualizar por ODEI y por mes",
                "enaho2015_cobertura_ind04_3",
                lambda f: [
                    f["sede"],
                    f["usuario"],
                    f["conglomerado"],
                    0,  # periodo: la pantalla actual siempre envía 0
                    mes(f["mes_inicio"]),
                    mes(f["mes_fin"]),
                    f["periodo_inicio"],
                    f["periodo_fin"],
                ],
            ),
        },
        procedimiento_mapa="enaho2015_tnr_parcial_map",
        prefijo="tnrp_",
        titulo_detalle="TNR Parcial (VALORES PORCENTUALES)",
        grafico={
            "titulo_barras": "% Tasa de No Respuesta Parcial",
            "eje_barras": "No Respuesta Parcial %",
            "serie_barras": "TNR_Parcial",
            "color_barras": "#C6CED8",
            "color_barra_ultima": "#7688A2",
            "titulo_lineas": "Tasa de No Respuesta Parcial",
            "eje_lineas": "% Tasa de no Respuesta Parcial",
            "etiqueta_mapa": "% TNR parcial",
        },
    )
)
