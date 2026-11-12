"""Configuración común. Todo lo sensible se lee de variables de entorno (.env)."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    # Módulos del sistema (uno por módulo del menú + uno común)
    "apps.comun",
    "apps.operacion_campo",
    "apps.reportes_campo",
    "apps.cobertura",
    "apps.calidad",
    "apps.valores_monetarios",
    "apps.seguimiento_monitor",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


def _sql_server(prefijo: str) -> dict:
    """Conexión a SQL Server con mssql-django, leída de variables DB_<PREFIJO>_*."""
    return {
        "ENGINE": "mssql",
        "NAME": env(f"DB_{prefijo}_NAME"),
        "HOST": env(f"DB_{prefijo}_HOST"),
        "PORT": env(f"DB_{prefijo}_PORT", default="1433"),
        "USER": env(f"DB_{prefijo}_USER"),
        "PASSWORD": env(f"DB_{prefijo}_PASSWORD"),
        "OPTIONS": {
            "driver": env("DB_ODBC_DRIVER", default="ODBC Driver 18 for SQL Server"),
            "extra_params": "TrustServerCertificate="
            + env("DB_TRUST_SERVER_CERTIFICATE", default="no"),
        },
    }


# Dos bases:
#  - default: base de monitoreo, propia del sistema nuevo (lectura y escritura).
#  - sistema_actual: la base del monitoreo actual (ENAHO2019_BDMONITOREO), SOLO LECTURA.
#    Ahí están los procedimientos y los usuarios del sistema actual. El router impide
#    escribir o migrar en ella.
DATABASES = {
    "default": _sql_server("MONITOREO"),
    "sistema_actual": _sql_server("ACTUAL"),
}
DATABASE_ROUTERS = ["config.db_routers.SistemaActualSoloLecturaRouter"]

AUTH_USER_MODEL = "comun.Usuario"

# Login: primero con las cuentas del sistema actual (solo lectura), luego con las locales.
AUTENTICAR_CON_SISTEMA_ACTUAL = env.bool("AUTENTICAR_CON_SISTEMA_ACTUAL", default=True)
SISTEMA_ACTUAL_TABLA_USUARIOS = env("SISTEMA_ACTUAL_TABLA_USUARIOS", default="dbo.usuarios_usuario")
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
if AUTENTICAR_CON_SISTEMA_ACTUAL:
    AUTHENTICATION_BACKENDS.insert(0, "apps.comun.autenticacion.UsuarioSistemaActualBackend")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# API REST: todo cerrado por defecto; cada vista abre lo que necesita.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.comun.excepciones.manejar_excepcion",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API Monitoreo ENAHO",
    "DESCRIPTION": "API REST del sistema de monitoreo de la Encuesta Nacional de Hogares.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Frontend Vue en otro origen durante el desarrollo
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Cookies: la sesión no es legible desde JavaScript. El token CSRF sí debe serlo
# para que el frontend lo envíe en la cabecera X-CSRFToken.
SESSION_COOKIE_HTTPONLY = True
# Nombres propios: las cookies se comparten entre todos los puertos de un mismo servidor
# (localhost:8000, localhost:5173...). Con los nombres por defecto de Django (sessionid,
# csrftoken) este sistema y el monitoreo actual, si corren en la misma máquina, se pisan
# la sesión uno al otro: al entrar en uno se cierra el otro.
SESSION_COOKIE_NAME = "enaho2027_sesion"
CSRF_COOKIE_NAME = "enaho2027_csrftoken"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 8  # una jornada

# Fuente de datos por módulo durante la migración (ver apps/<modulo>/repositorios.py)
FUENTE_COBERTURA = env("FUENTE_COBERTURA", default="sistema_actual")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
