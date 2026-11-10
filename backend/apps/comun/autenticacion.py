"""Login con los usuarios del sistema actual.

Mientras conviven los dos sistemas, el usuario entra con su mismo usuario y contraseña
de siempre. Este backend:

  1. Lee la cuenta en la tabla de usuarios del sistema actual (SOLO LECTURA).
  2. Verifica la contraseña contra el hash que guarda Django en esa tabla.
  3. Crea o actualiza una copia local del usuario (ODEI, cargo, permisos), SIN contraseña.

La contraseña nunca se copia: la fuente de verdad sigue siendo el sistema actual. Si una
cuenta no existe allí, se intenta con las cuentas locales (ModelBackend), por ejemplo el
administrador del sistema nuevo.
"""

import logging

from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.db import DatabaseError, connections

from config.db_routers import SISTEMA_ACTUAL

from .models import Usuario

log = logging.getLogger(__name__)

CAMPOS = ["usuario", "password", "is_active", "dni", "nombres", "apellidos", "email",
          "odei", "cargo", "permisos"]  # fmt: skip


def leer_usuario_actual(usuario: str) -> dict | None:
    tabla = settings.SISTEMA_ACTUAL_TABLA_USUARIOS
    columnas = ", ".join(f"[{c}]" for c in CAMPOS)
    sql = f"SELECT {columnas} FROM {tabla} WHERE [usuario] = %s"
    with connections[SISTEMA_ACTUAL].cursor() as cursor:
        cursor.execute(sql, [usuario])
        fila = cursor.fetchone()
    return dict(zip(CAMPOS, fila, strict=True)) if fila else None


class UsuarioSistemaActualBackend(BaseBackend):
    def authenticate(self, request, usuario=None, password=None, **kwargs):
        if not usuario or not password:
            return None
        try:
            cuenta = leer_usuario_actual(usuario)
        except DatabaseError:
            log.exception("No se pudo leer el usuario en el sistema actual")
            return None
        if not cuenta or not cuenta["is_active"] or not cuenta["password"]:
            return None
        if not check_password(password, cuenta["password"]):
            return None

        local, _ = Usuario.objects.get_or_create(usuario=cuenta["usuario"])
        for campo in ["dni", "nombres", "apellidos", "email", "odei", "cargo", "permisos"]:
            setattr(local, campo, (cuenta[campo] or "").strip())
        local.is_active = True
        local.set_unusable_password()
        local.save()
        return local

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id, is_active=True)
        except Usuario.DoesNotExist:
            return None
