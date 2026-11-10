"""De dónde salen los datos de cobertura.

Patrón Strangler Fig: hoy los datos salen de los procedimientos de la base del sistema actual
(RepositorioSistemaActual). Cuando existan las tablas resumen en la base de monitoreo, se
implementa RepositorioMonitoreo y se cambia FUENTE_COBERTURA en el .env. La API y el
frontend no cambian.
"""

from typing import Protocol

from django.conf import settings

from apps.comun import sistema_actual

from .indicadores import INDICADORES, Indicador

sistema_actual.registrar_procedimientos(
    *{p for i in INDICADORES.values() for p in i.procedimientos}
)


class RepositorioCobertura(Protocol):
    def consultar(self, indicador: Indicador, nivel: str, filtros: dict) -> list[dict]: ...

    def mapa(self, indicador: Indicador) -> list[dict]: ...


class RepositorioSistemaActual:
    """Lee de los procedimientos del sistema actual (ENAHO2019_BDMONITOREO, solo lectura)."""

    def consultar(self, indicador: Indicador, nivel: str, filtros: dict) -> list[dict]:
        consulta = indicador.niveles[nivel]
        return sistema_actual.ejecutar_procedimiento(
            consulta.procedimiento, consulta.armar(filtros)
        )

    def mapa(self, indicador: Indicador) -> list[dict]:
        return sistema_actual.ejecutar_procedimiento(indicador.mapa.procedimiento)


class RepositorioMonitoreo:
    """Lee de las tablas resumen de la base de monitoreo. Se implementa en la fase 2
    del piloto, cuando se conozca el código de los procedimientos."""

    def consultar(self, indicador: Indicador, nivel: str, filtros: dict) -> list[dict]:
        raise NotImplementedError("Tablas resumen de cobertura pendientes de diseño")

    def mapa(self, indicador: Indicador) -> list[dict]:
        raise NotImplementedError("Tablas resumen de cobertura pendientes de diseño")


class RepositorioDemo:
    """Datos de EJEMPLO (inventados) para desarrollar el frontend sin acceso a la base.
    Solo se activa con FUENTE_COBERTURA=demo (settings/demo.py). Nunca en producción."""

    DEPARTAMENTOS = [
        "AMAZONAS",
        "ANCASH",
        "APURIMAC",
        "AREQUIPA",
        "AYACUCHO",
        "CAJAMARCA",
        "CUSCO",
        "HUANCAVELICA",
        "HUANUCO",
        "ICA",
        "JUNIN",
        "LA LIBERTAD",
        "LAMBAYEQUE",
        "LIMA",
        "LORETO",
        "PIURA",
        "PUNO",
        "SAN MARTIN",
        "TACNA",
    ]

    def consultar(self, indicador: Indicador, nivel: str, filtros: dict) -> list[dict]:
        import random

        semilla = random.Random(f"{indicador.codigo}-{nivel}-{filtros.get('odei')}")
        nombres = (
            self.DEPARTAMENTOS
            if nivel == "departamento"
            else [f"ENCUESTADOR {i:02d}" for i in range(1, 13)]
        )
        filas = []
        for nombre in nombres:
            total = semilla.randint(80, 400)
            no_resp = semilla.randint(2, int(total * 0.2))
            filas.append(
                {
                    "nombre": nombre,
                    "viviendas_asignadas": total,
                    "no_respuesta": no_resp,
                    "tasa": round(100 * no_resp / total, 1),
                }
            )
        return filas

    def mapa(self, indicador: Indicador) -> list[dict]:
        import random

        semilla = random.Random(indicador.codigo)
        return [
            {
                "conglomerado": f"{i:06d}",
                "latitud": semilla.uniform(-16, -4),
                "longitud": semilla.uniform(-80, -70),
                "tasa": round(semilla.uniform(0, 25), 1),
            }
            for i in range(1, 60)
        ]


def obtener_repositorio() -> RepositorioCobertura:
    if settings.FUENTE_COBERTURA == "monitoreo":
        return RepositorioMonitoreo()
    if settings.FUENTE_COBERTURA == "demo":
        return RepositorioDemo()
    return RepositorioSistemaActual()
