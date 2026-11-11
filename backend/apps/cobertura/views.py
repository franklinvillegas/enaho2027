import re

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.constantes import Modulo
from apps.comun.exportar import respuesta_excel
from apps.comun.filtros import FiltrosIndicadorSerializer
from apps.comun.permisos import AccesoModulo

from . import excel_estrato, servicios, tnr_estrato, tnr_parcial, tnr_total  # noqa: F401
from . import tasas_no_respuesta as tnr
from .excel_tnr import respuesta_tnr
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


class TnrInfoView(BaseCobertura):
    """Metadatos de una pantalla de tasa de no respuesta: vistas, textos y gráficos."""

    @extend_schema(operation_id="cobertura_tnr_info", responses={200: dict})
    def get(self, request, indicador):
        return Response(tnr.obtener(indicador).info())


class TnrVistaView(BaseCobertura):
    """Filas de una vista, tal como las devuelve el procedimiento actual.

    Ejemplo: /api/v1/cobertura/tnr-parcial/odei-mes/?sede=15&usuario=0&mes_inicio=1&mes_fin=6
    Con &formato=xlsx devuelve el mismo resultado en Excel, con el diseño del reporte actual.
    """

    @extend_schema(
        operation_id="cobertura_tnr_vista",
        parameters=[
            tnr.FiltrosTnrSerializer,
            OpenApiParameter("formato", str, enum=["json", "xlsx"], required=False),
            OpenApiParameter("ambito", str, required=False, description="Título del Excel"),
        ],
        responses={200: dict},
    )
    def get(self, request, indicador, vista):
        config = tnr.obtener(indicador)
        datos = tnr.FiltrosTnrSerializer(data=request.query_params)
        datos.is_valid(raise_exception=True)
        filtros = dict(datos.validated_data)
        tnr.verificar_alcance(filtros, request.user)
        filas = tnr.consultar(config, vista, filtros)
        columnas = list(filas[0].keys()) if filas else []

        if request.query_params.get("formato") == "xlsx":
            ambito = re.sub(r"[^\w .,()\-]", "", request.query_params.get("ambito", ""))[:120]
            return respuesta_tnr(config, vista, filtros, filas, ambito.strip().upper())
        return Response({"vista": vista, "columnas": columnas, "filas": filas})


class TnrMapaView(BaseCobertura):
    @extend_schema(operation_id="cobertura_tnr_mapa", responses={200: dict})
    def get(self, request, indicador):
        return Response(tnr.consultar_mapa(tnr.obtener(indicador)))


# --- TNR según estrato ---------------------------------------------------------------


def _detalle(request) -> str:
    """Texto del pie del Excel (filtros elegidos), limpio y acotado."""
    return re.sub(r"[^\w .,:()\-]", "", request.query_params.get("detalle", ""))[:250].strip()


class TnrEstratoInfoView(BaseCobertura):
    @extend_schema(operation_id="cobertura_tnr_estrato_info", responses={200: dict})
    def get(self, request):
        return Response(tnr_estrato.info())


class TnrEstratoAnualView(BaseCobertura):
    """Pestaña RESUMEN ESTRATO: nacional > estrato > ODEI > conglomerados."""

    @extend_schema(
        operation_id="cobertura_tnr_estrato_anual",
        parameters=[tnr_estrato.FiltrosAnualSerializer],
        responses={200: dict},
    )
    def get(self, request):
        datos = tnr_estrato.FiltrosAnualSerializer(data=request.query_params)
        datos.is_valid(raise_exception=True)
        f = dict(datos.validated_data)
        tnr_estrato.verificar_alcance(f["odei"], request.user)
        filas = tnr_estrato.consultar_anual(f)
        if request.query_params.get("formato") == "xlsx":
            return excel_estrato.excel_anual(f, filas, _detalle(request))
        return Response({"filas": filas})


class TnrEstratoMensualView(BaseCobertura):
    """Pestaña RESUMEN POR MES: nacional > estrato > ODEI > conglomerado > viviendas."""

    @extend_schema(
        operation_id="cobertura_tnr_estrato_mensual",
        parameters=[tnr_estrato.FiltrosMensualSerializer],
        responses={200: dict},
    )
    def get(self, request):
        datos = tnr_estrato.FiltrosMensualSerializer(data=request.query_params)
        datos.is_valid(raise_exception=True)
        f = dict(datos.validated_data)
        tnr_estrato.verificar_alcance(f["odei"], request.user)
        filas = tnr_estrato.consultar_mensual(f)
        if request.query_params.get("formato") == "xlsx":
            return excel_estrato.excel_mensual(f, filas, _detalle(request))
        return Response({"filas": filas})


class TnrEstratoHogarView(BaseCobertura):
    """Pestaña RESUMEN TABULAR: hogares de una ODEI y mes."""

    @extend_schema(
        operation_id="cobertura_tnr_estrato_hogar",
        parameters=[tnr_estrato.FiltrosHogarSerializer],
        responses={200: dict},
    )
    def get(self, request):
        datos = tnr_estrato.FiltrosHogarSerializer(data=request.query_params)
        datos.is_valid(raise_exception=True)
        f = dict(datos.validated_data)
        tnr_estrato.verificar_alcance(f["odei"], request.user)
        filas = tnr_estrato.consultar_hogar(f)
        if request.query_params.get("formato") == "xlsx":
            return excel_estrato.excel_hogar(filas, _detalle(request))
        return Response({"filas": filas})
