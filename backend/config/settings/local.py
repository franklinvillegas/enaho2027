"""Modo LOCAL: datos reales del sistema actual, sin crear todavía la base de monitoreo.

- Lee procedimientos y usuarios de la base del sistema actual (ENAHO2019_BDMONITOREO),
  en SOLO LECTURA, con la conexión DB_ACTUAL_* del .env.
- Las tablas propias del sistema nuevo (sesiones, copia de usuarios, registro de uso)
  van a un SQLite local, hasta que exista la base de monitoreo nueva.
- Login con el mismo usuario y contraseña del sistema actual.

    python manage.py migrate --settings=config.settings.local
    python manage.py runserver --settings=config.settings.local
"""

import os

for _campo in ("NAME", "HOST", "USER", "PASSWORD"):
    os.environ.setdefault(f"DB_MONITOREO_{_campo}", "no-se-usa-en-local")

from .base import BASE_DIR  # noqa: E402
from .dev import *  # noqa: E402,F401,F403

DATABASES["default"] = {  # noqa: F405
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "local.sqlite3",
}
FUENTE_COBERTURA = "sistema_actual"
