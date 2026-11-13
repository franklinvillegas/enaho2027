"""Indicadores de calidad: mismo procedimiento y orden de parámetros que la pantalla actual."""

import pytest
from rest_framework.test import APIClient

from apps.comun import sistema_actual

BASE = "/api/v1/calidad/reportes/"


@pytest.fixture
def llamadas(monkeypatch):
    registro = []

    def falso(nombre, parametros=()):
        registro.append((nombre, list(parametros)))
        return [{"id": 0, "idMostrar": 0, "nombreMostrar": "NACIONAL"}]

    monkeypatch.setattr(sistema_actual, "ejecutar_procedimiento", falso)
    return registro


def _cliente(django_user_model, odei="00"):
    u = django_user_model.objects.create_user(
        usuario=f"prueba{odei}", password="x", permisos="1", cargo="09", odei=odei
    )
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.mark.django_db
def test_vivienda_hogar(django_user_model, llamadas):
    c = _cliente(django_user_model)
    c.get(BASE + "vivienda-hogar/departamentos/", {"indicador": 1})
    c.get(BASE + "vivienda-hogar/odei/", {"indicador": 4})
    c.get(BASE + "vivienda-hogar/odei/", {"indicador": 4, "sede": "14", "usuario": "12345678"})
    c.get(
        BASE + "vivienda-hogar/odei-mes/",
        {"indicador": 30, "sede": "8", "mes_inicio": 2, "mes_fin": 5, "periodo_fin": 3,
         "excluir": 3},
    )  # fmt: skip
    c.get(BASE + "vivienda-hogar/casos/", {"indicador": 66, "odei": "14", "mes_inicio": 1})
    assert llamadas == [
        ("enaho2017_calidad_11", []),
        ("enaho2017_calidad_42", ["0", ""]),
        ("enaho2017_calidad_42", ["14", "12345678"]),
        ("enaho2017_calidad_303", ["8", "", "0", "0", "3", "02", "05", "3"]),
        ("calidad_viviendaHogar_detalleBalanceHogar", ["14", "2", "0", "0", "01", "0"]),
    ]


@pytest.mark.django_db
def test_programas_sociales(django_user_model, llamadas):
    c = _cliente(django_user_model)
    params = {"indicador": 49, "sede": "3", "usuario": "4", "conglomerado": "001234"}
    c.get(BASE + "programas-sociales/odei-mes/", params)
    assert llamadas == [("enaho2017_calidad_493", ["3", "4", "001234", "0", "0", "0", "0", "0"])]


@pytest.mark.django_db
def test_indicador_o_vista_no_permitidos(django_user_model, llamadas):
    c = _cliente(django_user_model)
    assert c.get(BASE + "vivienda-hogar/odei/", {"indicador": 24}).status_code == 404
    assert c.get(BASE + "vivienda-hogar/casos/", {"indicador": 4}).status_code == 404
    assert c.get(BASE + "vivienda-hogar/otra/", {"indicador": 4}).status_code == 404
    assert c.get(BASE + "no-existe/odei/", {"indicador": 4}).status_code == 404
    assert c.get(BASE + "vivienda-hogar/odei/").status_code == 400  # falta el indicador
    assert llamadas == []


@pytest.mark.django_db
def test_usuario_de_odei_solo_ve_su_odei(django_user_model, llamadas):
    c = _cliente(django_user_model, odei="14")
    assert c.get(BASE + "vivienda-hogar/odei/", {"indicador": 4, "sede": "8"}).status_code == 403
    assert c.get(BASE + "vivienda-hogar/casos/", {"indicador": 65, "odei": "8"}).status_code == 403
    assert c.get(BASE + "vivienda-hogar/odei/", {"indicador": 4, "sede": "14"}).status_code == 200
