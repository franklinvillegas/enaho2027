from django.urls import path

from . import views

urlpatterns = [
    path("indicadores/", views.IndicadoresView.as_view(), name="cobertura-indicadores"),
    path("indicadores/<slug:codigo>/", views.IndicadorView.as_view(), name="cobertura-indicador"),
    path(
        "indicadores/<slug:codigo>/mapa/",
        views.MapaIndicadorView.as_view(),
        name="cobertura-indicador-mapa",
    ),
]
