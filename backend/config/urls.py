from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1 = [
    path("", include("apps.comun.urls")),
    path("operacion-campo/", include("apps.operacion_campo.urls")),
    path("reportes-campo/", include("apps.reportes_campo.urls")),
    path("cobertura/", include("apps.cobertura.urls")),
    path("calidad/", include("apps.calidad.urls")),
    path("valores-monetarios/", include("apps.valores_monetarios.urls")),
    path("seguimiento-monitor/", include("apps.seguimiento_monitor.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/esquema/", SpectacularAPIView.as_view(), name="esquema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="esquema"), name="docs"),
]
