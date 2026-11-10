import pytest
from rest_framework.test import APIClient

from apps.comun.acceso import modulos_permitidos
from apps.comun.constantes import Modulo


@pytest.fixture
def crear(django_user_model):
    def _crear(**campos):
        datos = {"permisos": "1", "cargo": "09", "odei": "00"} | campos
        return django_user_model.objects.create_user(
            usuario="u" + str(len(campos)), password="clave-segura-123", **datos
        )

    return _crear


@pytest.mark.django_db
def test_monitor_ve_todos_los_modulos(crear):
    assert modulos_permitidos(crear(cargo="09")) == Modulo.TODOS


@pytest.mark.django_db
def test_encuestador_no_ve_valores_monetarios_ni_seguimiento(crear):
    modulos = modulos_permitidos(crear(cargo="05"))
    assert Modulo.VALORES_MONETARIOS not in modulos
    assert Modulo.SEGUIMIENTO_MONITOR not in modulos
    assert Modulo.COBERTURA in modulos


@pytest.mark.django_db
def test_acceso_seguimiento_por_usuario(crear):
    assert Modulo.SEGUIMIENTO_MONITOR in modulos_permitidos(
        crear(cargo="05", acceso_seguimiento=True)
    )


@pytest.mark.django_db
def test_login_yo_y_logout(crear):
    crear()
    c = APIClient(enforce_csrf_checks=True)
    assert c.get("/api/v1/auth/csrf/").status_code == 204
    token = c.cookies["csrftoken"].value
    r = c.post(
        "/api/v1/auth/login/",
        {"usuario": "u0", "password": "clave-segura-123"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200, r.content
    assert r.json()["usuario"] == "u0"
    token = c.cookies["csrftoken"].value
    assert c.get("/api/v1/auth/yo/").json()["modulos"]
    assert c.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=token).status_code == 204
    assert c.get("/api/v1/auth/yo/").status_code == 403


@pytest.mark.django_db
def test_login_incorrecto(crear):
    crear()
    r = APIClient().post("/api/v1/auth/login/", {"usuario": "u0", "password": "mal"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_odei_regional_solo_ve_su_odei(crear):
    c = APIClient()
    c.force_authenticate(crear(odei="15"))
    assert [o["codigo"] for o in c.get("/api/v1/catalogos/odeis/").json()] == ["15"]


@pytest.mark.django_db
def test_registro_uso(crear):
    u = crear()
    c = APIClient()
    c.force_authenticate(u)
    r = c.post(
        "/api/v1/registro-uso/",
        {"pantalla": "cobertura/tnr-total", "evento": "ingreso"},
        format="json",
    )
    assert r.status_code == 201
    assert u.registros_uso.count() == 1


def test_api_sin_sesion_esta_cerrada():
    assert APIClient().get("/api/v1/cobertura/indicadores/").status_code == 403
