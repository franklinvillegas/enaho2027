import pytest
from rest_framework.test import APIClient

from apps.cobertura import tnr_total
from apps.comun import sistema_actual

BASE = "/api/v1/cobertura/tnr-total/"


@pytest.fixture
def llamadas(monkeypatch):
    registro = []

    def falso(nombre, parametros=()):
        registro.append((nombre, list(parametros)))
        return [{"idMostrar": 0, "nombreMostrar": "NACIONAL", "tnr2026": 7.0}]

    monkeypatch.setattr(sistema_actual, "ejecutar_procedimiento", falso)
    return registro


@pytest.fixture
def cliente(django_user_model):
    def _crear(**campos):
        datos = {"permisos": "1", "cargo": "09", "odei": "00"} | campos
        u = django_user_model.objects.create_user(usuario="prueba", password="x", **datos)
        c = APIClient()
        c.force_authenticate(u)
        return c

    return _crear


@pytest.mark.django_db
def test_vista_departamentos(cliente, llamadas):
    r = cliente().get(BASE + "departamentos/", {"mes_inicio": 1, "mes_fin": 6})
    assert r.status_code == 200
    assert r.json()["filas"][0]["nombreMostrar"] == "NACIONAL"
    assert llamadas == [("cobertura_tasaNoRespuestaTotal_dep", ["0", "0", "01", "06"])]


@pytest.mark.django_db
def test_vista_odei_nacional_y_sede(cliente, llamadas):
    c = cliente()
    c.get(BASE + "odei/")
    c.get(BASE + "odei/", {"sede": "15.1"})
    assert llamadas[0] == ("enaho2015_cobertura_ind03_2_v2", ["0", "0", "0", "0", "00", "00"])
    assert llamadas[1][1][:2] == ["15.1", "0"]


@pytest.mark.django_db
def test_vista_odei_mes_con_todos_los_parametros(cliente, llamadas):
    cliente().get(
        BASE + "odei-mes/",
        {"sede": "8", "usuario": "12345678", "conglomerado": "123456", "solo_activos": "true",
         "excluir": 2, "mes_inicio": 3, "mes_fin": 3, "periodo_inicio": 1, "periodo_fin": 2},
    )  # fmt: skip
    assert llamadas == [
        (
            "enaho2015_cobertura_ind03_3_v4",
            ["8", "12345678", "123456", "1", "2", "1", "03", "03", "2"],
        )
    ]


@pytest.mark.django_db
def test_vista_inexistente(cliente, llamadas):
    assert cliente().get(BASE + "otra/").status_code == 404


@pytest.mark.django_db
def test_odei_regional_ve_nacional_pero_no_otra_sede(cliente, llamadas):
    c = cliente(odei="08")
    assert c.get(BASE + "odei/").status_code == 200
    assert c.get(BASE + "odei/", {"sede": "8"}).status_code == 200
    assert c.get(BASE + "odei/", {"sede": "15"}).status_code == 403


@pytest.mark.django_db
def test_sede_con_inyeccion_rechazada(cliente, llamadas):
    assert cliente().get(BASE + "odei/", {"sede": "1;DROP"}).status_code == 400
    assert llamadas == []


def _hoja(respuesta):
    from io import BytesIO

    from openpyxl import load_workbook

    return load_workbook(BytesIO(respuesta.content)).active


@pytest.mark.django_db
def test_excel_con_el_diseno_del_reporte(cliente, llamadas):
    c = cliente()
    filas = c.get(BASE + "departamentos/").json()["filas"]
    llamadas.clear()
    r = c.post(
        BASE + "departamentos/excel/", {"filtros": {}, "filas": filas, "titulo": ""}, format="json"
    )
    assert llamadas == []  # el Excel usa las filas ya cargadas: no vuelve a consultar la base
    hoja = _hoja(r)
    assert hoja["A2"].value == "TNR TOTAL NACIONAL"
    encabezado = [hoja["A3"].value, hoja["B3"].value, hoja["C3"].value]
    assert encabezado == ["N°", "DOMINIOS DE ESTUDIO", "AÑOS"]
    assert hoja["C4"].value == "2026"
    assert hoja["B5"].value == "NACIONAL"
    assert hoja["B5"].fill.fgColor.rgb.endswith("F5FFBE")
    assert hoja["A6"].value == "FUENTE: SISTEMA MONITOREO ENAHO"
    assert hoja["A7"].value.startswith("FECHA Y HORA: ")


@pytest.mark.django_db
def test_excel_por_mes_agrupa_por_anio(cliente, monkeypatch):
    fila = {"idMostrar": 0, "nombreMostrar": "NACIONAL", "tnr2026": 7, "tnr2026_abs": 1873,
            "enero_2026": 5.5, "enero_2026_abs": 134}  # fmt: skip
    r = cliente().post(
        BASE + "odei-mes/excel/",
        {"filtros": {}, "filas": [fila], "titulo": "SEDE LIMA=1"},
        format="json",
    )
    hoja = _hoja(r)
    assert hoja["A2"].value == "TNR TOTAL SEDE LIMA1"
    assert hoja["C4"].value == 2026
    assert [hoja.cell(5, c).value for c in range(3, 7)] == ["Total", "Abs", "Ene", "Abs"]
    assert [hoja.cell(6, c).value for c in range(2, 7)] == ["NACIONAL", 7, 1873, 5.5, 134]


def test_etiquetas_de_columna():
    assert tnr_total.etiqueta_columna("tnr2026") == "2026"
    assert tnr_total.etiqueta_columna("enero_2026_abs") == "Ene 2026 (abs)"


@pytest.mark.django_db
def test_info_de_la_pantalla(cliente, llamadas):
    datos = cliente().get(BASE).json()
    assert [v["codigo"] for v in datos["vistas"]] == ["departamentos", "odei", "odei-mes"]
    assert "rechazo" in datos["formula"]


@pytest.mark.django_db
def test_excel_rechaza_filas_con_objetos_anidados(cliente):
    r = cliente().post(BASE + "odei/excel/", {"filas": [{"a": {"b": 1}}]}, format="json")
    assert r.status_code == 400
