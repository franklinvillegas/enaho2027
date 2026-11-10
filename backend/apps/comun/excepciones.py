import logging

from django.db import DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .sistema_actual import ProcedimientoNoPermitidoError

log = logging.getLogger(__name__)


def manejar_excepcion(exc, context):
    """Errores de base de datos: se registran completos en el log, pero al
    usuario solo se le devuelve un mensaje genérico (sin detalles del SQL)."""
    respuesta = exception_handler(exc, context)
    if respuesta is not None:
        return respuesta
    if isinstance(exc, ProcedimientoNoPermitidoError):
        log.error("Procedimiento no permitido: %s", exc)
        return Response({"detail": "Operación no permitida."}, status=status.HTTP_403_FORBIDDEN)
    if isinstance(exc, DatabaseError):
        log.exception("Error de base de datos en %s", context.get("view"))
        return Response(
            {"detail": "No se pudo obtener la información. Intente nuevamente."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return None
