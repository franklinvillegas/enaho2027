import pytest
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password

from apps.comun import autenticacion
from apps.comun.models import Usuario


def cuenta(**campos):
    base = {
        "usuario": "jperez",
        "password": make_password("clave-del-sistema-actual"),
        "is_active": True,
        "dni": "12345678",
        "nombres": "JUAN",
        "apellidos": "PEREZ",
        "email": "",
        "odei": "15",
        "cargo": "09",
        "permisos": "1",
    }
    return base | campos


@pytest.fixture
def sistema_actual(monkeypatch):
    cuentas = {}
    monkeypatch.setattr(autenticacion, "leer_usuario_actual", lambda u: cuentas.get(u))
    return cuentas


@pytest.mark.django_db
def test_entra_con_la_contrasena_del_sistema_actual_y_no_la_copia(sistema_actual):
    sistema_actual["jperez"] = cuenta()
    u = authenticate(None, usuario="jperez", password="clave-del-sistema-actual")
    assert u is not None
    assert (u.odei, u.cargo, u.permisos) == ("15", "09", "1")
    assert not u.has_usable_password()


@pytest.mark.django_db
def test_contrasena_incorrecta(sistema_actual):
    sistema_actual["jperez"] = cuenta()
    assert authenticate(None, usuario="jperez", password="otra") is None


@pytest.mark.django_db
def test_cuenta_desactivada_en_el_sistema_actual(sistema_actual):
    sistema_actual["jperez"] = cuenta(is_active=False)
    assert authenticate(None, usuario="jperez", password="clave-del-sistema-actual") is None


@pytest.mark.django_db
def test_los_cambios_de_cargo_se_actualizan_al_entrar(sistema_actual):
    sistema_actual["jperez"] = cuenta()
    authenticate(None, usuario="jperez", password="clave-del-sistema-actual")
    sistema_actual["jperez"] = cuenta(cargo="05")
    authenticate(None, usuario="jperez", password="clave-del-sistema-actual")
    assert Usuario.objects.get(usuario="jperez").cargo == "05"


@pytest.mark.django_db
def test_cuentas_locales_siguen_funcionando(sistema_actual, django_user_model):
    django_user_model.objects.create_user(usuario="admin", password="clave-local-123")
    assert authenticate(None, usuario="admin", password="clave-local-123") is not None
