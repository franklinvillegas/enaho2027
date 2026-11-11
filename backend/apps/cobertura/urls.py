from django.urls import path

from . import views
from .tasas_no_respuesta import REGISTRO

# Pantallas de tasa de no respuesta (tnr-total, tnr-parcial, ...): mismas rutas para todas.
#   /<indicador>/          vistas, textos y configuración de gráficos
#   /<indicador>/mapa/     mapa de calor por departamento
#   /<indicador>/<vista>/  filas de una vista (departamentos, odei, odei-mes); ?formato=xlsx
rutas_tnr = [
    ruta
    for codigo in REGISTRO
    for ruta in (
        path(f"{codigo}/", views.TnrInfoView.as_view(), {"indicador": codigo}, name=codigo),
        path(
            f"{codigo}/mapa/",
            views.TnrMapaView.as_view(),
            {"indicador": codigo},
            name=f"{codigo}-mapa",
        ),
        path(
            f"{codigo}/<slug:vista>/",
            views.TnrVistaView.as_view(),
            {"indicador": codigo},
            name=f"{codigo}-vista",
        ),
    )
]

# TNR según estrato: pantalla con cuatro pestañas (ver tnr_estrato.py)
rutas_estrato = [
    path("tnr-estrato/", views.TnrEstratoInfoView.as_view(), name="tnr-estrato"),
    path("tnr-estrato/anual/", views.TnrEstratoAnualView.as_view(), name="tnr-estrato-anual"),
    path("tnr-estrato/mensual/", views.TnrEstratoMensualView.as_view(), name="tnr-estrato-mensual"),
    path("tnr-estrato/hogar/", views.TnrEstratoHogarView.as_view(), name="tnr-estrato-hogar"),
]

urlpatterns = [
    *rutas_tnr,
    *rutas_estrato,
    path("indicadores/", views.IndicadoresView.as_view(), name="cobertura-indicadores"),
    path("indicadores/<slug:codigo>/", views.IndicadorView.as_view(), name="cobertura-indicador"),
    path(
        "indicadores/<slug:codigo>/mapa/",
        views.MapaIndicadorView.as_view(),
        name="cobertura-indicador-mapa",
    ),
]
