"""Pruebas automáticas: SQLite en memoria, sin SQL Server.

La lógica que toca la base del sistema actual se prueba con repositorios falsos
(ver apps/cobertura/tests).
"""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "clave-solo-para-pruebas")
for _base in ("MONITOREO", "ACTUAL"):
    for _campo in ("NAME", "HOST", "USER", "PASSWORD"):
        os.environ.setdefault(f"DB_{_base}_{_campo}", "pruebas")

from .base import *  # noqa: E402,F401,F403

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    "sistema_actual": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
