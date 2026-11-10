from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.constantes import Modulo
from apps.comun.exportar import respuesta_excel
from apps.comun.filtros import FiltrosIndicadorSerializer
from apps.comun.permisos import AccesoModulo

from . import servicios
from .indicadores import INDICADORES
from .repositorios import obtener_repositorio


class BaseCobertura(APIView):
    permission_classes = [AccesoModulo(Modulo.COBERTURA)]


class IndicadoresView(BaseCobertura):
    """Lista de indicadores del módulo, con sus niveles y si tienen mapa."""

    @extend_schema(operation_id="cobertura_indicadores_lista", responses={200: dict})
    def get(self, request):
        return Response(
            [
                {
                    "codigo": i.codigo,
                    "nombre": i.nombre,
                    "niveles": list(i.niveles),
                    "tiene_mapa": i.mapa is not None,
                }
                for i in INDICADORES.values()
            ]
        )


class IndicadorView(BaseCobertura):
    """Datos de un indicador en el nivel pedido.

    Ejemplo: /api/v1/cobertura/indicadores/tnr-total/?nivel=odei&odei=15
             &periodo_inicio=1&periodo_fin=3&mes_inicio=1&mes_fin=6
    Con &formato=xlsx devuelve el mismo resultado en Excel.
    """

    @extend_schema(
        operation_id="cobertura_indicador_datos",
        parameters=[
            FiltrosIndicadorSerializer,
            OpenApiParameter("formato", str, enum=["json", "xlsx"], required=False),
        ],
        responses={200: dict},
    )
    def get(self, request, codigo):
        filtros = FiltrosIndicadorSerializer(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        datos = filtros.aplicar_alcance(dict(filtros.validated_data), request.user)
        resultado = servicios.consultar_indicador(codigo, datos, obtener_repositorio())

        if request.query_params.get("formato") == "xlsx":
            return respuesta_excel(
                f"{codigo}_{resultado['nivel']}",
                resultado["nombre"],
                resultado["columnas"],
                resultado["filas"],
            )
        return Response(resultado)


class MapaIndicadorView(BaseCobertura):
    @extend_schema(operation_id="cobertura_indicador_mapa", responses={200: dict})
    def get(self, request, codigo):
        return Response(servicios.consultar_mapa(codigo, obtener_repositorio()))
