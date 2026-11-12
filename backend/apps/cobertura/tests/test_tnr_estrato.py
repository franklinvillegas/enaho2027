from io import BytesIO

import pytest
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.comun import sistema_actual

BASE = "/api/v1/cobertura/tnr-estrato/"


@pytest.fixture
def llamadas(monkeypatch):
    registro = []

    def falso(nombre, parametros=()):
        registro.append((nombre, list(parametros)))
        return [
            {"ORDEN": 0, "NOMBAREA": "TOTAL URBANO", "ESTRATO": 0, "TNR2026": 9.5,
             "TNR2026P": 8, "TNR2026P_ABS": 10, "TNR2026NP": 11, "TNR2026NP_ABS": 5},
            {"ORDEN": 1, "NOMBAREA": "TOTAL URBANO", "ESTRATO": 1, "TNR2026": 7,
             "TNR2026P": 6, "TNR2026P_ABS": 3, "TNR2026NP": 8, "TNR2026NP_ABS": 4},
        ]  # fmt: skip

    monkeypatch.setattr(sistema_actual, "ejecutar_procedimiento", falso)
    return registro


@pytest.fixture
def cliente(django_user_model):
    def _crear(odei="00"):
        u = django_user_model.objects.create_user(
            usuario=f"u{odei}", password="x", permisos="1", cargo="09", odei=odei
        )
        c = APIClient()
        c.force_authenticate(u)
        return c

    return _crear


@pytest.mark.django_db
def test_mismos_procedimientos_y_orden_que_la_pantalla_actual(cliente, llamadas):
    c = cliente()
    c.get(BASE + "anual/", {"mes_inicio": 1, "mes_fin": 6, "excluir": 2})
    c.get(BASE + "mensual/", {"tipo": 2, "estrato": 3, "odei": "15", "conglomerado": "123456",
                              "periodo_inicio": 1, "periodo_fin": 4})  # fmt: skip
    c.get(BASE + "hogar/", {"odei": 14, "mes": 3})
    assert llamadas == [
        ("ENAHO2017_TNR_ESTRATO_V3", ["0", "0", "00", "01", "0", "06", "0", "2"]),
        ("ENAHO2017_TNR_ESTRATO_MES_V3", ["2", "3", "15", "123456", "00", "1", "00", "4", "0"]),
        ("ENAHO2017_TNR_ESTRATO_HOGAR", ["14", "3"]),
    ]


@pytest.mark.django_db
def test_periodo_inicial_sin_final_se_rechaza(cliente, llamadas):
    r = cliente().get(BASE + "anual/", {"periodo_inicio": 2})
    assert r.status_code == 400
    assert llamadas == []


@pytest.mark.django_db
def test_odei_regional_solo_ve_su_odei(cliente, llamadas):
    c = cliente("14")
    assert c.get(BASE + "anual/", {"tipo": 1, "estrato": 1, "odei": "14"}).status_code == 200
    assert c.get(BASE + "anual/", {"tipo": 1, "estrato": 1, "odei": "15"}).status_code == 403
    assert c.get(BASE + "hogar/", {"odei": 15}).status_code == 403


@pytest.mark.django_db
def test_excel_anual_con_columnas_por_anio(cliente, llamadas):
    c = cliente()
    filas = c.get(BASE + "anual/").json()["filas"]
    llamadas.clear()
    r = c.post(
        BASE + "anual/excel/",
        {"filtros": {}, "filas": filas, "titulo": "NACIONAL URBANO"},
        format="json",
    )
    assert llamadas == []
    hoja = load_workbook(BytesIO(r.content)).active
    assert hoja["A2"].value == "TNR SEGÚN ESTRATO POR ODEI ANUAL"
    assert [hoja["A3"].value, hoja["B3"].value] == ["ESTRATOS SOCIOECONOMICOS", 2026]
    assert [hoja.cell(4, c).value for c in range(2, 8)] == [
        "TOTAL", "TOTAL_ABS", "PANEL", "PANEL_ABS", "NO PANEL", "NO PANEL_ABS",
    ]  # fmt: skip
    # TOTAL_ABS = panel + no panel, como la pantalla actual
    assert [hoja.cell(5, c).value for c in range(1, 8)] == ["TOTAL URBANO", 9.5, 15, 8, 10, 11, 5]
    assert hoja.cell(6, 1).value == "A (mas alto)"
