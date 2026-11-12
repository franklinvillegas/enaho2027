from io import BytesIO

import pytest
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.comun import sistema_actual

BASE = "/api/v1/cobertura/informacion-indirecta/"


@pytest.fixture
def llamadas(monkeypatch):
    registro = []

    def falso(nombre, parametros=()):
        registro.append((nombre, list(parametros)))
        return [{"idMostrar": 0, "nombreMostrar": "NACIONAL", "tii2026": 1.5}]

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
        {"sede": "8", "usuario": "12345678", "conglomerado": "123456", "solo_activos": "true",
         "mes_inicio": 3, "mes_fin": 4},
    )  # fmt: skip
    cliente.get(BASE + "absolutos/", {"sede": "8", "solo_activos": "true"})
    cliente.get(BASE + "mapa/")
    assert llamadas == [
        ("cobertura_tasaInformacionIndirecta_dep", ["0", "0", "01", "06"]),
        ("enaho2015_calidad_ind01_21", ["8", "0", "1", "2", "00", "00"]),
        ("enaho2015_calidad_ind01_31",
         ["8", "12345678", "123456", "0", "1", "0", "0", "03", "04"]),
        ("enaho2015_calidad_ind01_31_abs", ["8", "1", "0", "0", "00", "00"]),
        ("enaho2015_inf_indirecta_map", []),
    ]  # fmt: skip


@pytest.mark.django_db
def test_info(cliente, llamadas):
    datos = cliente.get(BASE).json()
    assert datos["titulo_pantalla"] == "INFORMACIÓN INDIRECTA"
    assert datos["filtros_extra"] == ["solo_activos"]
    assert datos["titulo_meses"] == "INFORMACIÓN INDIRECTA (VALORES PORCENTUALES)"
    assert datos["absolutos"]


@pytest.mark.django_db
def test_absolutos_solo_en_pantallas_que_lo_tienen(cliente, llamadas):
    assert cliente.get("/api/v1/cobertura/tnr-total/absolutos/").status_code == 404


@pytest.mark.django_db
def test_excel_por_mes_con_activo_y_titulo_propio(cliente):
    filas = [
        {"id": 0, "encuestador": "TOTAL", "tii2026": 2, "enero_2026": 1, "enero_2026_abs": 3},
        {"id": 1, "encuestador": "ANA", "activo": "SI", "usuario": "1", "tii2026": 4,
         "enero_2026": 2, "enero_2026_abs": 5},
    ]  # fmt: skip
    r = cliente.post(
        BASE + "odei-mes/excel/",
        {"filtros": {"sede": "8"}, "filas": filas, "titulo": "SEDE CUSCO"},
        format="json",
    )
    hoja = load_workbook(BytesIO(r.content)).active
    assert hoja["A2"].value == "REPORTE INFORMACIÓN INDIRECTA SEDE CUSCO"
    assert [hoja.cell(3, c).value for c in range(1, 5)] == [
        "N°", "ENCUESTADOR", "ACTIVO", "INFORMACIÓN INDIRECTA (VALORES PORCENTUALES)",
    ]  # fmt: skip
    assert [hoja.cell(7, c).value for c in range(1, 5)] == [1, "ANA", "SI", 4]


@pytest.mark.django_db
def test_excel_absolutos(cliente):
    filas = [{"nomencue": "ANA", "activo": "SI", "indirecta2026": 3, "tot2026": 90,
              "ind_ene2026": 1, "tot2026_1": 10}]  # fmt: skip
    r = cliente.post(BASE + "absolutos/excel/", {"filas": filas, "titulo": "SEDE CUSCO"},
                     format="json")  # fmt: skip
    hoja = load_workbook(BytesIO(r.content)).active
    assert hoja["C3"].value == "INFORMACIÓN INDIRECTA 2026 (VALORES ABSOLUTOS)"
    assert [hoja.cell(6, c).value for c in range(1, 7)] == ["ANA", "SI", 3, 90, 1, 10]
