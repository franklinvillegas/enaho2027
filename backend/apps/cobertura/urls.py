from django.urls import path

from . import views

urlpatterns = [
    path("tnr-total/", views.TnrTotalVistasView.as_view(), name="tnr-total"),
    path("tnr-total/mapa/", views.TnrTotalMapaView.as_view(), name="tnr-total-mapa"),
    path("tnr-total/<slug:vista>/", views.TnrTotalView.as_view(), name="tnr-total-vista"),
    path("indicadores/", views.IndicadoresView.as_view(), name="cobertura-indicadores"),
    path("indicadores/<slug:codigo>/", views.IndicadorView.as_view(), name="cobertura-indicador"),
    path(
        "indicadores/<slug:codigo>/mapa/",
        views.MapaIndicadorView.as_view(),
        name="cobertura-indicador-mapa",
    ),
]
