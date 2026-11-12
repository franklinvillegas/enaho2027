import re

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotFound
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

# --- Excel a partir de lo que la pantalla ya tiene ----------------------------------------


class ExcelSerializer(serializers.Serializer):
    """Filas ya cargadas en la pantalla + filtros con que se consultaron + título del archivo."""

    MAX_FILAS = 50_000

    filtros = serializers.DictField(default=dict)
    filas = serializers.ListField(child=serializers.DictField(), max_length=MAX_FILAS)
    titulo = serializers.CharField(allow_blank=True, default="", max_length=500)

    def validate_filas(self, filas):
        # Solo valores simples (texto, número, vacío): nada de objetos anidados
        for fila in filas:
            if len(fila) > 200 or any(
                v is not None and not isinstance(v, str | int | float | bool) for v in fila.values()
            ):
                raise serializers.ValidationError("Formato de filas no válido.")
        return filas


def _validar(serializer, datos) -> dict:
    s = serializer(data=datos)
    s.is_valid(raise_exception=True)
    return dict(s.validated_data)


def _texto_limpio(texto: str, largo: int) -> str:
    """Texto para el título o pie del Excel, sin caracteres raros y acotado."""
    return re.sub(r"[^\w .,:()\-]", "", texto)[:largo].strip()


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
    """

    @extend_schema(
        operation_id="cobertura_tnr_vista",
        parameters=[tnr.FiltrosTnrSerializer],
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
        return Response({"vista": vista, "columnas": columnas, "filas": filas})


class TnrExcelView(BaseCobertura):
    """Excel de la tabla que la pantalla YA cargó: no vuelve a consultar la base.

    La pantalla envía las filas que tiene en memoria, los filtros (para saber el nivel y
    las columnas) y el título; aquí solo se arma el archivo con el diseño del reporte actual.
    """

    @extend_schema(
        operation_id="cobertura_tnr_excel", request=ExcelSerializer, responses={200: bytes}
    )
    def post(self, request, indicador, vista):
        config = tnr.obtener(indicador)
        if vista not in config.vistas:
            raise NotFound(f"Vista '{vista}' no existe.")
        datos = ExcelSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        filtros = _validar(tnr.FiltrosTnrSerializer, datos.validated_data["filtros"])
        ambito = _texto_limpio(datos.validated_data["titulo"], 120).upper()
        return respuesta_tnr(config, vista, filtros, datos.validated_data["filas"], ambito)


class TnrMapaView(BaseCobertura):
    @extend_schema(operation_id="cobertura_tnr_mapa", responses={200: dict})
    def get(self, request, indicador):
        return Response(tnr.consultar_mapa(tnr.obtener(indicador)))


# --- TNR según estrato ---------------------------------------------------------------


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
        return Response({"filas": filas})


class TnrEstratoExcelView(BaseCobertura):
    """Excel de una pestaña con las filas que la pantalla YA cargó (no consulta la base)."""

    FILTROS = {
        "anual": tnr_estrato.FiltrosAnualSerializer,
        "mensual": tnr_estrato.FiltrosMensualSerializer,
        "hogar": tnr_estrato.FiltrosHogarSerializer,
    }

    @extend_schema(
        operation_id="cobertura_tnr_estrato_excel", request=ExcelSerializer, responses={200: bytes}
    )
    def post(self, request, tabla):
        if tabla not in self.FILTROS:
            raise NotFound(f"Tabla '{tabla}' no existe.")
        datos = ExcelSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        f = _validar(self.FILTROS[tabla], datos.validated_data["filtros"])
        filas = datos.validated_data["filas"]
        detalle = _texto_limpio(datos.validated_data["titulo"], 250)
        if tabla == "hogar":
            return excel_estrato.excel_hogar(filas, detalle)
        generar = excel_estrato.excel_anual if tabla == "anual" else excel_estrato.excel_mensual
        return generar(f, filas, detalle)
