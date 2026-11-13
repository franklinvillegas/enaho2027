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


@pytest.mark.django_db
def test_demograficos(django_user_model, llamadas):
    from datetime import date

    a = date.today().year
    c = _cliente(django_user_model)
    c.get(BASE + "demograficos/piramide/", {"indicador": 100, "departamento": "08", "mes_inicio": 1,
                                            "mes_fin": 3})  # fmt: skip
    c.get(BASE + "demograficos/casos/", {"indicador": 67, "odei": "14"})
    c.get(BASE + "demograficos/odei/", {"indicador": 13})
    assert llamadas == [
        ("enaho2020_calidad_piramide_edad", [str(a), "08", "0", "0", "01", "03", "0"]),
        ("enaho2020_calidad_piramide_edad", [str(a - 1), "08", "0", "0", "01", "03", "0"]),
        ("enaho2020_calidad_piramide_edad", [str(a - 2), "08", "0", "0", "01", "03", "0"]),
        ("calidad_demografico_detalleMiembrosHogar", ["14", "0", "0", "0", "0"]),
        ("enaho2017_calidad_132", ["0", ""]),
    ]


@pytest.mark.django_db
def test_consumo_de_alimentos(django_user_model, llamadas):
    c = _cliente(django_user_model)
    c.get(
        BASE + "consumo-alimentos/precios/", {"indicador": 43, "anio": 2025, "odei": "8", "mes": 3}
    )
    params = {"indicador": 43, "anio": 2025, "odei": "8", "mes": 3, "producto": "100037"}
    c.get(BASE + "consumo-alimentos/precios-provincias/", params)
    c.get(BASE + "consumo-alimentos/precios-lista/", params)
    c.get(BASE + "consumo-alimentos/casos/", {"indicador": 68, "periodo_fin": 2})
    c.get(BASE + "consumo-alimentos/odei-mes/", {"indicador": 44, "excluir": 5})
    assert llamadas == [
        ("enaho2017_calidad_diferenciaPrecios", ["2025", "08", "03"]),
        ("enaho2018_calidad_preciosProvincias", ["2025", "03", "08", "100037"]),
        ("enaho2018_calidad_preciosLista", ["2025", "03", "08", "100037"]),
        ("calidad_consumoHogar_detalleGastosCanasta", ["0", "0", "2", "0", "0"]),
        ("enaho2017_calidad_443", ["0", "", "0", "0", "0", "0", "0", "5"]),
    ]


@pytest.mark.django_db
def test_educacion_tasa_de_asistencia(django_user_model, llamadas):
    c = _cliente(django_user_model)
    c.get(BASE + "educacion/departamentos/", {"indicador": 91, "dominio": 2})
    c.get(BASE + "educacion/odei-mes/", {"indicador": 91, "dominio": 3, "sede": "8",
                                         "usuario": "12345678"})  # fmt: skip
    c.get(BASE + "educacion/odei/", {"indicador": 14})
    assert llamadas == [
        # Por departamento no hay dominio, como la pantalla actual
        ("enaho2020_calidad_tasaasistenciaescolar_10", ["0", "0", "0", "0", "0", "0", "0", "0"]),
        (
            "enaho2020_calidad_tasaasistenciaescolar_33",
            ["8", "12345678", "0", "0", "0", "0", "0", "0"],
        ),  # fmt: skip
        ("enaho2017_calidad_142", ["0", ""]),
    ]


@pytest.mark.django_db
def test_salud_razones(django_user_model, llamadas):
    c = _cliente(django_user_model)
    c.get(BASE + "salud/odei/", {"indicador": 72})
    assert llamadas == [("enaho2017_calidad_722", ["0", ""])]


@pytest.mark.django_db
def test_empleo(django_user_model, llamadas):
    c = _cliente(django_user_model)
    c.get(BASE + "empleo/odei-mes/", {"indicador": 31, "sede": "8"})
    c.get(BASE + "empleo/departamentos/", {"indicador": 31})
    c.get(BASE + "empleo/odei/", {"indicador": 36, "mes_inicio": 2, "mes_fin": 2, "excluir": 1})
    c.get(BASE + "empleo/trimestral/", {"indicador": 42, "sede": "8", "usuario": "12345678"})
    c.get(BASE + "empleo/pet/", {"indicador": 42, "sede": "8"})
    c.get(BASE + "empleo/encuestadores/", {"indicador": 42, "sede": "8"})
    rango = ["8", "", "0", "0", "0", "0", "0", "0"]
    assert llamadas == [
        ("enaho2017_calidad_313_se", rango),
        ("enaho2017_calidad_313_st", rango),
        ("enaho2017_calidad_313_et", rango),
        ("enaho2017_calidad_313_nini", rango),
        ("enaho2017_calidad_311", []),
        ("enaho2017_calidad_362", ["0", "0", "02", "02", "1"]),
        ("enaho2017_calidad_421", ["8", "12345678"]),
        ("Calidad_EmpleoOtros_PetSegunCondicionActividad_anual", ["8", "0"]),
        ("Calidad_EmpleoOtros_PetSegunCondicionActividad_mensual", ["8", "0"]),
        ("enaho_usuario_monitoreo", ["8", "prueba00"]),
    ]


@pytest.mark.django_db
def test_varias_llamadas_marcan_su_grupo(django_user_model, llamadas):
    c = _cliente(django_user_model)
    filas = c.get(BASE + "empleo/odei-mes/", {"indicador": 31}).json()["filas"]
    assert [f["grupo"] for f in filas] == ["se", "st", "et", "nini"]


@pytest.mark.django_db
def test_excel_con_varias_tablas(django_user_model):
    from io import BytesIO

    from openpyxl import load_workbook

    c = _cliente(django_user_model)
    seccion = {"titulo": "SOLO ESTUDIAN", "encabezados": [[{"texto": "ODEI"}, {"texto": "2026"}]],
               "filas": [{"celdas": ["NACIONAL", "12.5"], "total": True}]}  # fmt: skip
    r = c.post(
        "/api/v1/excel/", {"titulo": "EMPLEO", "secciones": [seccion, seccion]}, format="json"
    )
    hoja = load_workbook(BytesIO(r.content)).active
    assert [hoja["A3"].value, hoja["A4"].value, hoja["B5"].value] == ["SOLO ESTUDIAN", "ODEI", 12.5]
    assert hoja["A7"].value == "SOLO ESTUDIAN"
