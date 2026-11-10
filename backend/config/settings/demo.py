"""Modo DEMO: para trabajar el frontend sin SQL Server ni VPN.

Usa SQLite local para usuarios y datos de EJEMPLO inventados para los indicadores.

    python manage.py migrate --settings=config.settings.demo
    python manage.py createsuperuser --settings=config.settings.demo
    python manage.py runserver --settings=config.settings.demo
"""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "clave-solo-para-demo")
for _base in ("MONITOREO", "CAPTURA"):
    for _campo in ("NAME", "HOST", "USER", "PASSWORD"):
        os.environ.setdefault(f"DB_{_base}_{_campo}", "demo")

from .base import BASE_DIR  # noqa: E402
from .dev import *  # noqa: E402,F401,F403

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "demo.sqlite3"},
    "captura": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
FUENTE_COBERTURA = "demo"
