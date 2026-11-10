from rest_framework.permissions import BasePermission

from .acceso import puede_acceder


def AccesoModulo(modulo: str):  # noqa: N802 - se usa como clase de permiso
    """Permiso DRF: el usuario puede usar el módulo indicado.

    Uso en una vista:  permission_classes = [AccesoModulo(Modulo.COBERTURA)]
    """

    class _Acceso(BasePermission):
        message = "No tiene acceso a este módulo."

        def has_permission(self, request, view):
            return puede_acceder(request.user, modulo)

    _Acceso.__name__ = f"AccesoModulo_{modulo}"
    return _Acceso
