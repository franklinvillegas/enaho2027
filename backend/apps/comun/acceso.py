"""Reglas de acceso por módulo según el cargo del usuario.

Traducen las condiciones que hoy están dispersas en el menú del sistema actual
(templates/webclient/layouts/sidebar.html). Viven en un solo lugar y se aplican
en dos sitios: el backend (permiso de cada endpoint) y el frontend (qué opciones
del menú se muestran, vía /api/v1/auth/yo/).

Pendiente de validar con el área usuaria: el menú actual además da acceso a
"Seguimiento del monitor" a una lista fija de nombres de usuario. Aquí eso se
reemplaza por el campo Usuario.acceso_seguimiento, que se marca en el admin.
"""

from .constantes import Cargo, Modulo, Permiso

C = Cargo

# Cargos SIN acceso a cada módulo (None = sin restricción adicional)
_EXCLUIDOS = {
    Modulo.OPERACION_CAMPO: {C.UDRA},
    Modulo.REPORTES_CAMPO: {C.UDRA},
    Modulo.COBERTURA: set(),
    Modulo.CALIDAD: set(),
    Modulo.VALORES_MONETARIOS: {
        C.ENCUESTADOR,
        C.SUPERVISOR_LOCAL,
        C.COORDINADOR_DEPARTAMENTAL,
        C.DIRECTOR,
    },
}

# Cargos CON acceso (lista cerrada)
_PERMITIDOS = {
    Modulo.SEGUIMIENTO_MONITOR: {
        C.JEFE_OPERACION_CAMPO,
        C.JEFE_PROYECTO,
        C.METODOLOGO,
        C.MONITOR,
        C.OPERADOR_PROCESOS,
    },
}


def puede_acceder(usuario, modulo: str) -> bool:
    if not usuario or not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    if usuario.permisos not in (Permiso.SUPERVISAR, Permiso.ENCUESTAR):
        return False
    if modulo in _PERMITIDOS:
        return usuario.cargo in _PERMITIDOS[modulo] or (
            modulo == Modulo.SEGUIMIENTO_MONITOR and usuario.acceso_seguimiento
        )
    return usuario.cargo not in _EXCLUIDOS.get(modulo, set())


def modulos_permitidos(usuario) -> list[str]:
    return [m for m in Modulo.TODOS if puede_acceder(usuario, m)]
