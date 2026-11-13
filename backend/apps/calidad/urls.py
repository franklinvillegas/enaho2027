"""Indicadores de calidad.

Vivienda y hogar, demográficos, consumo de alimentos, programas sociales, educación, salud
y empleo. Todas siguen el mismo esquema (ver indicadores.py).
"""

from django.urls import path

from .views import ReporteCalidadView

urlpatterns = [
    path(
        "reportes/<slug:pantalla>/<slug:vista>/",
        ReporteCalidadView.as_view(),
        name="calidad-reporte",
    ),
]
