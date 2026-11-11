from io import BytesIO

import pytest
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.comun import sistema_actual

BASE = "/api/v1/cobertura/tnr-parcial/"


@pytest.fixture
def llamadas(monkeypatch):
    registro = []

    def falso(nombre, parametros=()):
        registro.append((nombre, list(parametros)))
        return [{"idMostrar": 0, "nombreMostrar": "NACIONAL", "tnrp_2026": 3.4, "tnrp_2026_abs": 9}]

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
        {"sede": "8", "usuario": "12345678", "conglomerado": "123456",
         "mes_inicio": 3, "mes_fin": 4, "periodo_inicio": 1, "periodo_fin": 5},
    )  # fmt: skip
    assert llamadas == [
        ("cobertura_tasaNoRespuestaParcial_dep", ["0", "0", "01", "06"]),
        ("enaho2015_cobertura_ind04_2", ["8", "0", "1", "2", "00", "00"]),
        ("enaho2015_cobertura_ind04_3", ["8", "12345678", "123456", "0", "03", "04", "1", "5"]),
    ]


@pytest.mark.django_db
def test_mapa(cliente, llamadas):
    assert cliente.get(BASE + "mapa/").status_code == 200
    assert llamadas == [("enaho2015_tnr_parcial_map", [])]


@pytest.mark.django_db
def test_info_sin_filtros_extra(cliente, llamadas):
    datos = cliente.get(BASE).json()
    assert datos["prefijo"] == "tnrp_"
    assert datos["filtros_extra"] == []
    assert datos["grafico"]["color_barra_ultima"] == "#7688A2"
    assert "capítulos 300" in datos["descripcion"]


@pytest.mark.django_db
def test_excel_con_absoluto_por_anio(cliente, llamadas):
    r = cliente.get(BASE + "departamentos/", {"formato": "xlsx"})
    hoja = load_workbook(BytesIO(r.content)).active
    assert hoja["A2"].value == "TNR PARCIAL NACIONAL"
    assert [hoja["C4"].value, hoja["D4"].value] == ["2026", "Abs."]
    assert [hoja["C5"].value, hoja["D5"].value] == [3.4, 9]
    assert r["Content-Disposition"].endswith('tnr-parcial_departamentos.xlsx"')


@pytest.mark.django_db
def test_excel_detalle_de_conglomerado(cliente, monkeypatch):
    filas = [
        {"id": 0, "tnrp_2026": 8.9},
        {"id": 1, "mes": "03", "conglomerado": "123456", "vivienda": "001", "hogar": "11",
         "tnrp_2026": 100},
    ]  # fmt: skip
    monkeypatch.setattr(sistema_actual, "ejecutar_procedimiento", lambda *a, **k: filas)
    r = cliente.get(
        BASE + "odei-mes/",
        {"formato": "xlsx", "sede": "15", "usuario": "12345678", "conglomerado": "123456"},
    )
    hoja = load_workbook(BytesIO(r.content)).active
    assert [hoja.cell(3, c).value for c in range(1, 7)] == [
        "N°", "MES", "CONGLOMERADO", "VIVIENDA", "HOGAR", "TNR Parcial (VALORES PORCENTUALES)",
    ]  # fmt: skip
    assert [hoja.cell(6, c).value for c in range(1, 7)] == [1, "03", "123456", "001", "11", 100]
