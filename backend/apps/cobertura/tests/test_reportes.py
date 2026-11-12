"""Control de visitas, omisión por capítulos, omisiones GPS y tipo de entrevista.

Se comprueba que cada vista llame al mismo procedimiento que la pantalla actual, con los
parámetros en el mismo orden y formato, y el Excel genérico de tablas (/api/v1/excel/).
"""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.comun import sistema_actual

BASE = "/api/v1/cobertura/reportes/"


@pytest.fixture
def llamadas(monkeypatch):
    registro = []

    def falso(nombre, parametros=()):
        registro.append((nombre, list(parametros)))
        return [{"id": 0, "nombreMostrar": "NACIONAL"}]

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
def test_control_de_visitas(cliente, llamadas):
    cliente.get(BASE + "control-visitas/departamentos/", {"mes_inicio": 1, "mes_fin": 6})
    cliente.get(BASE + "control-visitas/odei/", {"sede": "8"})
    cliente.get(
        BASE + "control-visitas/odei-mes/", {"sede": "8", "periodo_inicio": 2, "excluir": 1}
    )
    cliente.get(BASE + "control-visitas/casos/", {"sede": "14", "mes_inicio": 3, "mes_fin": 3})
    assert llamadas == [
        ("cobertura_controlVisitas_dep", ["0", "0", "01", "06"]),
        ("enaho2016_visitas_odei_anio", ["8", "00"]),
        ("enaho2016_visitas_odei_mes", ["8", "00", "2", "0", "00", "00", "1"]),
        ("cobertura_controlVisitas_casos", ["14", "0", "0", "03", "03"]),
    ]


@pytest.mark.django_db
def test_omision_por_capitulos(cliente, llamadas):
    cliente.get(BASE + "omision-capitulos/grafico/", {"sede": "0"})
    cliente.get(BASE + "omision-capitulos/anio/", {"sede": "8", "usuario": "12345678"})
    cliente.get(BASE + "omision-capitulos/mes/", {"sede": "8", "mes_inicio": 2, "mes_fin": 5})
    cliente.get(BASE + "omision-capitulos/mapa/")
    assert llamadas == [
        ("enaho2015_calidad_ind02", ["00", "0"]),
        ("ENAHO2020_CALIDAD_OMISIONCAPITULOS_ANIO", ["8", "12345678"]),
        ("ENAHO2020_CALIDAD_OMISIONCAPITULOS_MES", ["8", "0", "0", "0", "0", "02", "05"]),
        ("enaho2015_omision_capitulo_map", []),
    ]


@pytest.mark.django_db
def test_omisiones_gps(cliente, llamadas):
    cliente.get(BASE + "omisiones-gps/resumen/", {"sede": "0", "mes": 4, "periodo": 2})
    cliente.get(
        BASE + "omisiones-gps/viviendas/",
        {"sede": "8", "usuario": "12345678", "conglomerado": "001234", "mes": 5},
    )
    assert llamadas == [
        ("enaho2016_geo_omisiones", ["00", "0", "04", "2"]),
        ("enaho2015_cobertura_ind01_2", [str(date.today().year), "8", "001234", "05", "0"]),
    ]


@pytest.mark.django_db
def test_tipo_de_entrevista(cliente, llamadas):
    cliente.get(BASE + "tipo-entrevista/departamentos/", {"periodo_inicio": 1, "periodo_fin": 3})
    cliente.get(BASE + "tipo-entrevista/odei/", {"sede": "8", "usuario": "12345678"})
    cliente.get(BASE + "tipo-entrevista/odei-mes/", {"sede": "0"})
    assert llamadas == [
        ("cobertura_tipoEntrevista_dep", ["1", "3", "00", "00"]),
        ("enaho2021_tipoEntrevista_odei", ["8", "12345678", "0"]),
        ("enaho2021_tipoEntrevista_odeiMes", ["0", "0", "0"]),
    ]


@pytest.mark.django_db
def test_pantalla_o_vista_desconocida(cliente, llamadas):
    assert cliente.get(BASE + "no-existe/odei/").status_code == 404
    assert cliente.get(BASE + "control-visitas/no-existe/").status_code == 404
    assert llamadas == []


@pytest.mark.django_db
def test_excel_de_tabla(cliente):
    tabla = {
        "titulo": "CONTROL DE VISITA - ÁMBITO NACIONAL",
        "nombre_archivo": "CONTROL-DE-VISITA",
        "color": "1565C0",
        "encabezados": [
            [
                {"texto": "N°", "filas": 2},
                {"texto": "ODEI", "filas": 2},
                {"texto": "2026", "columnas": 2},
            ],
            [{"texto": "Visitas"}, {"texto": "Minutos"}],
        ],  # fmt: skip
        "filas": [
            {"celdas": ["", "NACIONAL", "1.8", "62.5"], "total": True},
            {"celdas": ["08", "CUSCO", "2.1", "=1+1"], "resaltadas": [3]},
        ],
        "pie": ["SELECCIÓN: Mes inicial: enero"],
    }
    r = cliente.post("/api/v1/excel/", tabla, format="json")
    assert r.status_code == 200
    assert 'filename="CONTROL-DE-VISITA.xlsx"' in r["Content-Disposition"]
    hoja = load_workbook(BytesIO(r.content)).active
    assert hoja["A2"].value == "CONTROL DE VISITA - ÁMBITO NACIONAL"
    assert "C3:D3" in {str(m) for m in hoja.merged_cells.ranges}
    assert hoja["C4"].value == "Visitas"
    assert hoja["C5"].value == 1.8 and hoja["C5"].fill.fgColor.rgb.endswith("F5FFBE")
    assert hoja["A6"].value == "08"  # el código ODEI queda como texto
    assert hoja["D6"].value == "'=1+1"  # nada de fórmulas
    assert hoja["D6"].font.color.rgb.endswith("FF2400")
    assert hoja["A7"].value == "FUENTE: SISTEMA MONITOREO ENAHO"


@pytest.mark.django_db
def test_excel_de_tabla_valida_datos(cliente):
    r = cliente.post("/api/v1/excel/", {"titulo": "X", "encabezados": [], "filas": [],
                                        "nombre_archivo": "../etc"}, format="json")  # fmt: skip
    assert r.status_code == 400
