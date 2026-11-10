"""Casos de uso del módulo. No conocen SQL ni HTTP: reciben filtros validados y un
repositorio, y devuelven datos. Así se pueden probar con un repositorio falso."""

from rest_framework.exceptions import NotFound, ValidationError

from .indicadores import INDICADORES, Indicador
from .repositorios import RepositorioCobertura


def obtener_indicador(codigo: str) -> Indicador:
    try:
        return INDICADORES[codigo]
    except KeyError:
        raise NotFound(f"Indicador '{codigo}' no existe.") from None


def consultar_indicador(codigo: str, filtros: dict, repositorio: RepositorioCobertura) -> dict:
    indicador = obtener_indicador(codigo)
    nivel = filtros["nivel"]
    if nivel not in indicador.niveles:
        disponibles = ", ".join(indicador.niveles)
        raise ValidationError({"nivel": f"Niveles disponibles para este indicador: {disponibles}."})
    filas = repositorio.consultar(indicador, nivel, filtros)
    return {
        "indicador": indicador.codigo,
        "nombre": indicador.nombre,
        "nivel": nivel,
        "columnas": list(filas[0].keys()) if filas else [],
        "filas": filas,
    }


def consultar_mapa(codigo: str, repositorio: RepositorioCobertura) -> list[dict]:
    indicador = obtener_indicador(codigo)
    if indicador.mapa is None:
        raise NotFound("Este indicador no tiene mapa.")
    return repositorio.mapa(indicador)
