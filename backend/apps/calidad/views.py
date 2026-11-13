from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.constantes import Modulo
from apps.comun.permisos import AccesoModulo

from . import servicios
from .indicadores import obtener


class ReporteCalidadView(APIView):
    """Filas de un indicador de calidad en una vista.

    Vistas: departamentos · odei · odei-mes · casos (solo los indicadores que lo tienen).
    Ejemplo: /api/v1/calidad/reportes/vivienda-hogar/odei-mes/?indicador=4&sede=14
    """

    permission_classes = [AccesoModulo(Modulo.CALIDAD)]

    @extend_schema(
        operation_id="calidad_reporte",
        parameters=[servicios.FiltrosCalidadSerializer],
        responses={200: dict},
    )
    def get(self, request, pantalla, vista):
        s = servicios.FiltrosCalidadSerializer(data=request.query_params)
        s.is_valid(raise_exception=True)
        f = dict(s.validated_data)
        obtener(pantalla, vista, f["indicador"])
        servicios.verificar_alcance(f, request.user)
        return Response({"filas": servicios.consultar(pantalla, vista, f)})
