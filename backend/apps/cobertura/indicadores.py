"""Catálogo de indicadores de cobertura.

Cada indicador declara, por nivel de detalle, qué procedimiento del sistema actual lo
calcula y en qué orden recibe los parámetros. Es el "contrato" con el sistema actual
mientras dura la migración: cuando un indicador pase a la base de monitoreo, solo cambia
el repositorio, no la API ni el frontend.

Origen: monitoreo-enaho-v2, consultasdb/api/views.py (clases sp_tnrTotal_t1, _t2, _t3, ...).
Formato de los parámetros igual al que envían las pantallas actuales
(static/.../tasaNoRespuesta/tnr_total.js): meses con dos dígitos ("01".."12", "00" = sin
filtro), periodo 0..5 (0 = todos) y "0" en los opcionales vacíos (corrección VUL-004).
"""

from dataclasses import dataclass, field

from apps.comun.filtros import Nivel


def _mes(valor) -> str:
    return f"{int(valor or 0):02d}"


def _rango(f):
    return [f["periodo_inicio"], f["periodo_fin"], _mes(f["mes_inicio"]), _mes(f["mes_fin"])]


def _odei(f):
    return [f.get("odei") or "0", f.get("encuestador") or "0"]


@dataclass(frozen=True)
class Consulta:
    procedimiento: str
    parametros: callable = field(default=lambda f: [])

    def armar(self, filtros: dict) -> list:
        return [str(p) for p in self.parametros(filtros)]


@dataclass(frozen=True)
class Indicador:
    codigo: str
    nombre: str
    niveles: dict  # Nivel -> Consulta
    mapa: Consulta | None = None

    @property
    def procedimientos(self) -> set[str]:
        nombres = {c.procedimiento for c in self.niveles.values()}
        if self.mapa:
            nombres.add(self.mapa.procedimiento)
        return nombres


INDICADORES: dict[str, Indicador] = {
    i.codigo: i
    for i in [
        # TNR total y parcial tienen su propia pantalla con vistas: ver tnr_total.py,
        # tnr_parcial.py y tasas_no_respuesta.py.
        # Los siguientes indicadores tienen por ahora solo el nivel departamento.
        # Los niveles ODEI y conglomerado se agregan cuando se confirme el orden
        # de parámetros con el código de cada procedimiento.
        Indicador(
            codigo="problemas-marco",
            nombre="Tasa de problemas de marco",
            niveles={Nivel.DEPARTAMENTO: Consulta("cobertura_tasaProblemasMarco_dep", _rango)},
            mapa=Consulta("enaho2015_tpm_map"),
        ),
        Indicador(
            codigo="informacion-indirecta",
            nombre="Tasa de información indirecta",
            niveles={
                Nivel.DEPARTAMENTO: Consulta("cobertura_tasaInformacionIndirecta_dep", _rango)
            },
            mapa=Consulta("enaho2015_inf_indirecta_map"),
        ),
        Indicador(
            codigo="control-visitas",
            nombre="Control de visitas",
            niveles={Nivel.DEPARTAMENTO: Consulta("cobertura_controlVisitas_dep", _rango)},
        ),
        Indicador(
            codigo="tipo-entrevista",
            nombre="Tipo de entrevista",
            niveles={Nivel.DEPARTAMENTO: Consulta("cobertura_tipoEntrevista_dep", _rango)},
        ),
    ]
}
