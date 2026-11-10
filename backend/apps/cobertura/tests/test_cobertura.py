import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.cobertura import repositorios, servicios
from apps.cobertura.indicadores import INDICADORES
from apps.comun import sistema_actual
from apps.comun.filtros import Nivel

URL = "/api/v1/cobertura/indicadores/tnr-total/"
RANGO = {"periodo_inicio": 1, "periodo_fin": 3, "mes_inicio": 1, "mes_fin": 6}
TODO = {"periodo_inicio": 0, "periodo_fin": 0, "mes_inicio": 0, "mes_fin": 0}


class RepositorioFalso:
    """Reemplaza a la base del sistema actual en las pruebas y guarda lo que se le pidió."""

    def __init__(self):
        self.llamadas = []

    def consultar(self, indicador, nivel, filtros):
        consulta = indicador.niveles[nivel]
        self.llamadas.append((consulta.procedimiento, consulta.armar(filtros)))
        return [{"departamento": "LIMA", "tasa": 12.5}]

    def mapa(self, indicador):
        return [{"ubigeo": "15", "valor": 12.5}]


@pytest.fixture
def repo(monkeypatch):
    falso = RepositorioFalso()
    monkeypatch.setattr("apps.cobertura.views.obtener_repositorio", lambda: falso)
    return falso


@pytest.fixture
def cliente(django_user_model):
    def _crear(**campos):
        datos = {"permisos": "1", "cargo": "09", "odei": "00"} | campos
        usuario = django_user_model.objects.create_user(usuario="prueba", password="x", **datos)
        c = APIClient()
        c.force_authenticate(usuario)
        return c

    return _crear


@pytest.mark.django_db
def test_nivel_departamento_llama_al_procedimiento_actual_con_parametros_en_orden(cliente, repo):
    r = cliente().get(URL, {"nivel": "departamento", **RANGO})
    assert r.status_code == 200
    assert r.json()["filas"][0]["departamento"] == "LIMA"
    assert repo.llamadas == [("cobertura_tasaNoRespuestaTotal_dep", ["1", "3", "01", "06"])]


@pytest.mark.django_db
def test_nivel_conglomerado_usa_ceros_en_opcionales(cliente, repo):
    r = cliente().get(URL, {"nivel": "conglomerado", "odei": "15", **RANGO})
    assert r.status_code == 200
    proc, params = repo.llamadas[0]
    assert proc == "enaho2015_cobertura_ind03_3_v4"
    assert params == ["15", "0", "0", "1", "3", "0", "01", "06", "0"]


@pytest.mark.django_db
def test_usuario_de_una_odei_solo_ve_su_odei(cliente, repo):
    cliente(odei="08").get(URL, {"nivel": "odei", "odei": "15", **RANGO})
    assert repo.llamadas[0][1][0] == "08"


@pytest.mark.django_db
def test_parametro_con_inyeccion_es_rechazado(cliente, repo):
    r = cliente().get(
        URL, {"nivel": "conglomerado", "odei": "15", "conglomerado": "1'; DROP--", **RANGO}
    )
    assert r.status_code == 400
    assert repo.llamadas == []


@pytest.mark.django_db
def test_encuestador_no_tiene_acceso_a_otro_modulo_pero_si_a_cobertura(cliente, repo):
    c = cliente(cargo="05")
    assert c.get(URL, {"nivel": "departamento", **RANGO}).status_code == 200


@pytest.mark.django_db
def test_usuario_deshabilitado_no_accede(cliente, repo):
    r = cliente(permisos="0").get(URL, {"nivel": "departamento", **RANGO})
    assert r.status_code == 403


@pytest.mark.django_db
def test_exporta_excel(cliente, repo):
    r = cliente().get(URL, {"nivel": "departamento", "formato": "xlsx", **RANGO})
    assert r.status_code == 200
    assert r["Content-Type"].startswith("application/vnd.openxmlformats")


def test_nivel_no_disponible():
    with pytest.raises(ValidationError):
        servicios.consultar_indicador(
            "tipo-entrevista", {"nivel": Nivel.ODEI, **RANGO}, RepositorioFalso()
        )


def test_todos_los_procedimientos_estan_en_la_lista_blanca():
    assert repositorios  # importar el módulo registra la lista blanca
    for indicador in INDICADORES.values():
        assert indicador.procedimientos <= sistema_actual.PROCEDIMIENTOS_PERMITIDOS


def test_sistema_actual_rechaza_procedimientos_fuera_de_la_lista():
    with pytest.raises(sistema_actual.ProcedimientoNoPermitidoError):
        sistema_actual.ejecutar_procedimiento("sp_cualquiera")


@pytest.mark.django_db
def test_sin_filtros_envia_todos_como_las_pantallas_actuales(cliente, repo):
    r = cliente().get(URL, {"nivel": "departamento"})
    assert r.status_code == 200
    assert repo.llamadas == [("cobertura_tasaNoRespuestaTotal_dep", ["0", "0", "00", "00"])]


@pytest.mark.django_db
def test_mes_final_anterior_al_inicial_es_rechazado(cliente, repo):
    r = cliente().get(URL, {"nivel": "departamento", **TODO, "mes_inicio": 6, "mes_fin": 2})
    assert r.status_code == 400
    assert repo.llamadas == []
