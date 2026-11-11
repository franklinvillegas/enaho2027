import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.cobertura import repositorios, servicios
from apps.cobertura.indicadores import INDICADORES
from apps.comun import sistema_actual
from apps.comun.filtros import Nivel

URL = "/api/v1/cobertura/indicadores/problemas-marco/"
RANGO = {"periodo_inicio": 1, "periodo_fin": 3, "mes_inicio": 1, "mes_fin": 6}


class RepositorioFalso:
    """Reemplaza a la base del sistema actual y guarda lo que se le pidió."""

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
def test_parametros_con_el_formato_del_sistema_actual(cliente, repo):
    r = cliente().get(URL, {"nivel": "departamento", **RANGO})
    assert r.status_code == 200
    assert repo.llamadas == [("cobertura_tasaProblemasMarco_dep", ["1", "3", "01", "06"])]


@pytest.mark.django_db
def test_sin_filtros_envia_todos(cliente, repo):
    assert cliente().get(URL).status_code == 200
    assert repo.llamadas == [("cobertura_tasaProblemasMarco_dep", ["0", "0", "00", "00"])]


@pytest.mark.django_db
def test_mes_final_anterior_al_inicial_es_rechazado(cliente, repo):
    r = cliente().get(URL, {"mes_inicio": 6, "mes_fin": 2})
    assert r.status_code == 400
    assert repo.llamadas == []


@pytest.mark.django_db
def test_encuestador_tiene_acceso_a_cobertura(cliente, repo):
    assert cliente(cargo="05").get(URL).status_code == 200


@pytest.mark.django_db
def test_usuario_deshabilitado_no_accede(cliente, repo):
    assert cliente(permisos="0").get(URL).status_code == 403


@pytest.mark.django_db
def test_exporta_excel(cliente, repo):
    r = cliente().get(URL, {"formato": "xlsx"})
    assert r.status_code == 200
    assert r["Content-Type"].startswith("application/vnd.openxmlformats")


def test_nivel_no_disponible():
    with pytest.raises(ValidationError):
        servicios.consultar_indicador(
            "tipo-entrevista", {"nivel": Nivel.ODEI, **RANGO}, RepositorioFalso()
        )


def test_todos_los_procedimientos_estan_en_la_lista_blanca():
    assert repositorios
    for indicador in INDICADORES.values():
        assert indicador.procedimientos <= sistema_actual.PROCEDIMIENTOS_PERMITIDOS


def test_sistema_actual_rechaza_procedimientos_fuera_de_la_lista():
    with pytest.raises(sistema_actual.ProcedimientoNoPermitidoError):
        sistema_actual.ejecutar_procedimiento("sp_cualquiera")
