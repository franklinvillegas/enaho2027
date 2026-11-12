from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from . import excel_tabla
from .constantes import ODEI_NACIONAL, ODEIS
from .serializers import LoginSerializer, RegistroUsoSerializer, UsuarioActualSerializer


class LoginThrottle(AnonRateThrottle):
    rate = "10/min"


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """Entrega la cookie CSRF al frontend antes del login."""

    permission_classes = [AllowAny]

    @extend_schema(responses={204: None})
    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(request=LoginSerializer, responses=UsuarioActualSerializer)
    def post(self, request):
        datos = LoginSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        usuario = authenticate(
            request,
            usuario=datos.validated_data["usuario"],
            password=datos.validated_data["password"],
        )
        if usuario is None:
            return Response(
                {"detail": "Usuario o contraseña incorrectos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, usuario)
        return Response(UsuarioActualSerializer(usuario).data)


class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class YoView(APIView):
    """Usuario en sesión y módulos a los que tiene acceso (arma el menú)."""

    @extend_schema(responses=UsuarioActualSerializer)
    def get(self, request):
        return Response(UsuarioActualSerializer(request.user).data)


class OdeisView(APIView):
    """ODEI que el usuario puede consultar: todas si es nacional, si no solo la suya."""

    @extend_schema(responses={200: dict})
    def get(self, request):
        odeis = [{"codigo": c, "nombre": n} for c, n in ODEIS if c != ODEI_NACIONAL]
        if not request.user.es_nacional:
            odeis = [o for o in odeis if o["codigo"] == request.user.odei]
        return Response(odeis)


class RegistroUsoView(APIView):
    """Reemplaza a insertarIngreso / insertarSalida del sistema actual."""

    @extend_schema(request=RegistroUsoSerializer, responses={201: None})
    def post(self, request):
        datos = RegistroUsoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        datos.save(usuario=request.user)
        return Response(status=status.HTTP_201_CREATED)


class ExcelTablaView(APIView):
    """Excel de una tabla que la pantalla ya cargó (no consulta la base)."""

    @extend_schema(request=excel_tabla.TablaExcelSerializer, responses={200: bytes})
    def post(self, request):
        datos = excel_tabla.TablaExcelSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        return excel_tabla.respuesta(datos.validated_data)
