"""Indicadores de calidad: qué indicadores tiene cada pantalla y qué procedimiento llama.

En el sistema actual (consultasdb/api/views.py: IndicadoresViviendaHogar,
IndicadoresProgramasSociales, ...) todas estas pantallas llaman al mismo esquema de
procedimientos, armando el nombre con el código del indicador y la vista:

    enaho2017_calidad_{indicador}{tipo}
      tipo 1  Departamentos     sin parámetros
      tipo 2  ODEI (por año)    sede, encuestador
      tipo 3  ODEI y por mes    sede, encuestador, conglomerado, periodo inicial,
                                periodo final, mes inicial, mes final, exclusiones

Aquí cada pantalla declara la lista cerrada de indicadores que acepta: así el nombre del
procedimiento nunca se arma con un valor que venga del navegador sin validar, y todos
quedan registrados en la lista blanca de apps.comun.sistema_actual.

Formato de parámetros igual al de la pantalla actual: sede "0" = todas, encuestador ""
= todos, conglomerado "0" = todos, meses "0" o "01".."12", periodos 0..5, excluir 0..3.
"""

from dataclasses import dataclass, field

from rest_framework.exceptions import NotFound

from apps.comun import sistema_actual

VISTAS = {"departamentos": 1, "odei": 2, "odei-mes": 3}


@dataclass(frozen=True)
class Pantalla:
    codigo: str
    indicadores: tuple[int, ...]
    # Indicadores con "Visualizar casos": código → tipo que recibe el procedimiento
    casos: dict[int, int] = field(default_factory=dict)
    procedimiento_casos: str = ""


PANTALLAS = {
    p.codigo: p
    for p in (
        # viviendaHogar.js
        Pantalla(
            "vivienda-hogar",
            (1, 3, 16, 4, 5, 30, 32, 33, 34, 35, 65, 66),
            casos={65: 1, 66: 2},  # 1 = déficit, 2 = superávit
            procedimiento_casos="calidad_viviendaHogar_detalleBalanceHogar",
        ),
        # seguimientoProgramasSociales.js
        Pantalla("programas-sociales", (24, 49)),
    )
}


def procedimiento(indicador: int, vista: str) -> str:
    return f"enaho2017_calidad_{indicador}{VISTAS[vista]}"


for _p in PANTALLAS.values():
    sistema_actual.registrar_procedimientos(
        *(procedimiento(i, v) for i in _p.indicadores for v in VISTAS)
    )
    if _p.procedimiento_casos:
        sistema_actual.registrar_procedimientos(_p.procedimiento_casos)


def obtener(pantalla: str, vista: str, indicador: int) -> Pantalla:
    p = PANTALLAS.get(pantalla)
    if p is None:
        raise NotFound(f"La pantalla '{pantalla}' no existe.")
    if indicador not in p.indicadores:
        raise NotFound(f"El indicador {indicador} no pertenece a '{pantalla}'.")
    if vista == "casos":
        if indicador not in p.casos:
            raise NotFound(f"El indicador {indicador} no tiene detalle de casos.")
    elif vista not in VISTAS:
        raise NotFound(f"La vista '{vista}' no existe.")
    return p
