"""Catálogo de indicadores de cobertura.

Cada indicador declara, por nivel de detalle, qué procedimiento del sistema actual lo
calcula y en qué orden recibe los parámetros. Es el "contrato" con el sistema actual
mientras dura la migración: cuando un indicador pase a la base de monitoreo, solo cambia
el repositorio, no la API ni el frontend.

Origen: monitoreo-enaho-v2, consultasdb/api/views.py (clases sp_tnrTotal_t1, _t2, _t3, ...).
Los valores por defecto de los parámetros opcionales ("0") siguen la corrección VUL-004
del sistema actual. Se confirman con el código de los procedimientos.
"""

from dataclasses import dataclass, field

from apps.comun.filtros import Nivel


def _rango(f):
    return [f["periodo_inicio"], f["periodo_fin"], f["mes_inicio"], f["mes_fin"]]


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
        Indicador(
            codigo="tnr-total",
            nombre="Tasa de no respuesta total",
            niveles={
                Nivel.DEPARTAMENTO: Consulta("cobertura_tasaNoRespuestaTotal_dep", _rango),
                Nivel.ODEI: Consulta(
                    "enaho2015_cobertura_ind03_2_v2", lambda f: _odei(f) + _rango(f)
                ),
                Nivel.CONGLOMERADO: Consulta(
                    "enaho2015_cobertura_ind03_3_v4",
                    lambda f: (
                        _odei(f)
                        + [
                            f.get("conglomerado") or "0",
                            f["periodo_inicio"],
                            f["periodo_fin"],
                            "1" if f.get("solo_activos") else "0",
                            f["mes_inicio"],
                            f["mes_fin"],
                            f.get("excluir") or "0",
                        ]
                    ),
                ),
            },
            mapa=Consulta("enaho2015_tnr_total_map"),
        ),
        # Los siguientes indicadores tienen por ahora solo el nivel departamento.
        # Los niveles ODEI y conglomerado se agregan cuando se confirme el orden
        # de parámetros con el código de cada procedimiento.
        Indicador(
            codigo="tnr-parcial",
            nombre="Tasa de no respuesta parcial",
            niveles={Nivel.DEPARTAMENTO: Consulta("cobertura_tasaNoRespuestaParcial_dep", _rango)},
            mapa=Consulta("enaho2015_tnr_parcial_map"),
        ),
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
