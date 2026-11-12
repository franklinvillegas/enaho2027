from io import BytesIO

import pytest
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.comun import sistema_actual

BASE = "/api/v1/cobertura/problemas-marco/"


@pytest.fixture
def llamadas(monkeypatch):
    registro = []

    def falso(nombre, parametros=()):
        registro.append((nombre, list(parametros)))
        return [{"idMostrar": 0, "nombreMostrar": "NACIONAL", "tpm_2025": 3.1, "tpm_2026": 2.7}]

    monkeypatch.setattr(sistema_actual, "ejecutar_procedimiento", falso)
    return registro


@pytest.fixture
def cliente(django_user_model):
    u = django_user_model.objects.create_user(
        usuario="prueba", password="x", permisos="1", cargo="09", odei="00"
    )
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.mark.django_db
def test_mismos_procedimientos_y_orden_que_la_pantalla_actual(cliente, llamadas):
    cliente.get(BASE + "departamentos/", {"mes_inicio": 1, "mes_fin": 6})
    cliente.get(BASE + "odei/", {"sede": "8", "periodo_inicio": 1, "periodo_fin": 2})
    cliente.get(
        BASE + "odei-mes/",
        {"sede": "8", "usuario": "12345678", "conglomerado": "123456", "mes_inicio": 3,
         "mes_fin": 4},
    )  # fmt: skip
    cliente.get(BASE + "mapa/")
    assert llamadas == [
        ("cobertura_tasaProblemasMarco_dep", ["0", "0", "01", "06"]),
        ("enaho2015_cobertura_ind02_2", ["8", "0", "1", "2", "00", "00"]),
        ("enaho2015_cobertura_ind02_3", ["8", "12345678", "123456", "0", "0", "03", "04"]),
        ("enaho2015_tpm_map", []),
    ]


@pytest.mark.django_db
def test_info(cliente, llamadas):
    datos = cliente.get(BASE).json()
    assert datos["prefijo"] == "tpm_"
    assert datos["filtros_extra"] == []
    assert datos["colorear_ultimo"] is True
    assert "result 5,6,7" in datos["formula"]


@pytest.mark.django_db
def test_excel(cliente, llamadas):
    filas = cliente.get(BASE + "departamentos/").json()["filas"]
    r = cliente.post(BASE + "departamentos/excel/", {"filas": filas}, format="json")
    hoja = load_workbook(BytesIO(r.content)).active
    assert hoja["A2"].value == "TASA DE PROBLEMAS DE MARCO NACIONAL"
    assert [hoja["C4"].value, hoja["D4"].value] == ["2025", "2026"]
    assert hoja["D5"].fill.fgColor.rgb.endswith("DCF2FD")  # escala azul en el último año
