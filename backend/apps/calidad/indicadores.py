"""Indicadores de calidad: qué indicadores tiene cada pantalla y qué procedimiento llama.

En el sistema actual (consultasdb/api/views.py: IndicadoresViviendaHogar,
IndicadoresDemograficos, ...) casi todos los indicadores usan el mismo esquema de
procedimientos, armando el nombre con el código del indicador y la vista:

    enaho2017_calidad_{indicador}{tipo}
      tipo 1  Departamentos     sin parámetros
      tipo 2  ODEI (por año)    sede, encuestador
      tipo 3  ODEI y por mes    sede, encuestador, conglomerado, periodo inicial,
                                periodo final, mes inicial, mes final, exclusiones

Algunos indicadores tienen además (o en lugar de eso) consultas propias: "Visualizar casos",
pirámide de edad, precios, tasa de asistencia escolar, etc. Se declaran como `especiales`:
(indicador, vista) → la lista de llamadas a procedimientos que hace la pantalla actual,
en el mismo orden.

Cada pantalla declara la lista cerrada de indicadores que acepta: así el nombre del
procedimiento nunca se arma con un valor que venga del navegador sin validar, y todos
quedan registrados en la lista blanca de apps.comun.sistema_actual.

Formato de parámetros igual al de la pantalla actual: sede "0" = todas, encuestador ""
= todos, conglomerado "0" = todos, meses "0" o "01".."12", periodos 0..5, excluir 0..5.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from rest_framework.exceptions import NotFound

from apps.comun import sistema_actual

VISTAS = {"departamentos": 1, "odei": 2, "odei-mes": 3}


@dataclass(frozen=True)
class Llamada:
    procedimiento: str
    parametros: list
    # Columnas que se agregan a cada fila (p. ej. el año de la pirámide o el grupo)
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Pantalla:
    codigo: str
    # Indicadores con el esquema común enaho2017_calidad_{indicador}{tipo}
    indicadores: tuple[int, ...]
    # (indicador, vista) → función que recibe los filtros y devuelve las llamadas
    especiales: dict[tuple[int, str], Callable[[dict], list[Llamada]]] = field(default_factory=dict)
    # Procedimientos que usan los especiales (para la lista blanca)
    procedimientos: tuple[str, ...] = ()

    def acepta(self, indicador: int) -> bool:
        return indicador in self.indicadores or any(i == indicador for i, _ in self.especiales)


# ---------------------------------------------------------------------------------------
# Formato de parámetros
# ---------------------------------------------------------------------------------------


def mes(m: int) -> str:
    # La pantalla actual manda "0" cuando no se eligió mes y "01".."12" si se eligió
    return f"{m:02d}" if m else "0"


def todos(valor, vacio: str) -> str:
    return vacio if str(valor) in ("0", "00", "") else str(valor)


def rango(f: dict) -> list[str]:
    return [str(f["periodo_inicio"]), str(f["periodo_fin"]), mes(f["mes_inicio"]),
            mes(f["mes_fin"])]  # fmt: skip


def procedimiento(indicador: int, vista: str, sufijo: str = "") -> str:
    return f"enaho2017_calidad_{indicador}{VISTAS[vista]}{sufijo}"


def parametros_estandar(vista: str, f: dict) -> list[str]:
    sede = todos(f["sede"], "0")
    usuario = todos(f["usuario"], "")
    if vista == "departamentos":
        return []
    if vista == "odei":
        return [sede, usuario]
    return [sede, usuario, f["conglomerado"], *rango(f), str(f["excluir"])]


def _odei(f: dict) -> str:
    return todos(f["odei"], "0")


def _casos(proc: str, *antes) -> Callable[[dict], list[Llamada]]:
    """Visualizar casos: ODEI del combo, [tipo], periodos y meses."""
    return lambda f: [Llamada(proc, [_odei(f), *[str(a) for a in antes], *rango(f)])]


# ---------------------------------------------------------------------------------------
# Especiales de cada pantalla
# ---------------------------------------------------------------------------------------

BALANCE = "calidad_viviendaHogar_detalleBalanceHogar"
MIEMBROS = "calidad_demografico_detalleMiembrosHogar"
CANASTA = "calidad_consumoHogar_detalleGastosCanasta"
PIRAMIDE = "enaho2020_calidad_piramide_edad"
PRECIOS = "enaho2017_calidad_diferenciaPrecios"
PRECIOS_PROVINCIAS = "enaho2018_calidad_preciosProvincias"
PRECIOS_LISTA = "enaho2018_calidad_preciosLista"
PET_ANUAL = "Calidad_EmpleoOtros_PetSegunCondicionActividad_anual"
PET_MENSUAL = "Calidad_EmpleoOtros_PetSegunCondicionActividad_mensual"
ENCUESTADORES = "enaho_usuario_monitoreo"
NINI = ("se", "st", "et", "nini")  # solo estudian, solo trabajan, ambos, ni uno ni otro


def _asistencia(v: int, d: int) -> str:
    return f"enaho2020_calidad_tasaasistenciaescolar_{v}{d}"


def _piramide(f: dict) -> list[Llamada]:
    # La pantalla actual dibuja una pirámide por año: el actual y los dos anteriores
    anio = date.today().year
    return [
        Llamada(
            PIRAMIDE,
            [str(a), f["departamento"], *rango(f), str(f["excluir"])],
            {"anio_piramide": a},
        )  # fmt: skip
        for a in (anio, anio - 1, anio - 2)
    ]


def _precios(proc: str, con_producto: bool) -> Callable[[dict], list[Llamada]]:
    def llamadas(f: dict) -> list[Llamada]:
        odei = f"{int(f['odei'] or 1):02d}"
        if not con_producto:  # diferenciaPrecios: año, ODEI, mes
            return [Llamada(proc, [str(f["anio"]), odei, f"{f['mes'] or 1:02d}"])]
        return [Llamada(proc, [str(f["anio"]), f"{f['mes'] or 1:02d}", odei, f["producto"]])]

    return llamadas


def _asistencia_escolar(vista: str) -> Callable[[dict], list[Llamada]]:
    v = VISTAS[vista]

    def llamadas(f: dict) -> list[Llamada]:
        d = f["dominio"] if v != 1 else 0
        return [Llamada(_asistencia(v, d), [
            todos(f["sede"], "0"), todos(f["usuario"], "0"), f["conglomerado"], *rango(f),
            str(f["excluir"]),
        ])]  # fmt: skip

    return llamadas


def _nini(f: dict) -> list[Llamada]:
    # Situación laboral de 15 a 24 años por mes: cuatro tablas, una por grupo
    return [
        Llamada(
            procedimiento(31, "odei-mes", f"_{g}"), parametros_estandar("odei-mes", f), {"grupo": g}
        )  # fmt: skip
        for g in NINI
    ]


def _etnicidad(vista: str) -> Callable[[dict], list[Llamada]]:
    return lambda f: [Llamada(procedimiento(36, vista), [*rango(f), str(f["excluir"])])]


def _pet(f: dict) -> list[Llamada]:
    p = [todos(f["sede"], "0"), todos(f["usuario"], "0")]
    return [
        Llamada(PET_ANUAL, p, {"serie": "anual"}),
        Llamada(PET_MENSUAL, p, {"serie": "mensual"}),
    ]


PANTALLAS = {
    p.codigo: p
    for p in (
        # viviendaHogar.js
        Pantalla(
            "vivienda-hogar",
            (1, 3, 16, 4, 5, 30, 32, 33, 34, 35, 65, 66),
            especiales={(65, "casos"): _casos(BALANCE, 1), (66, "casos"): _casos(BALANCE, 2)},
            procedimientos=(BALANCE,),
        ),
        # demograficos.js (9 = pirámide de edad, código 100 en la pantalla actual)
        Pantalla(
            "demograficos",
            (6, 13, 2, 7, 8, 25, 17, 18, 67),
            especiales={(100, "piramide"): _piramide, (67, "casos"): _casos(MIEMBROS)},
            procedimientos=(PIRAMIDE, MIEMBROS),
        ),
        # consumoAlimentosHogar.js
        Pantalla(
            "consumo-alimentos",
            (44, 22, 46, 45, 48, 68),
            especiales={
                (43, "precios"): _precios(PRECIOS, False),
                (43, "precios-provincias"): _precios(PRECIOS_PROVINCIAS, True),
                (43, "precios-lista"): _precios(PRECIOS_LISTA, True),
                (68, "casos"): _casos(CANASTA),
            },
            procedimientos=(PRECIOS, PRECIOS_PROVINCIAS, PRECIOS_LISTA, CANASTA),
        ),
        # seguimientoProgramasSociales.js
        Pantalla("programas-sociales", (24, 49)),
        # seguimientoEducacion.js (91 = tasa de asistencia escolar, con dominio)
        Pantalla(
            "educacion",
            (14, 50, 51, 52, 53, 54, 55, 9, 10),
            especiales={(91, v): _asistencia_escolar(v) for v in VISTAS},
            procedimientos=tuple(_asistencia(v, d) for v in (1, 2, 3) for d in (0, 1, 2, 3)),
        ),
        # seguimientoSalud.js (57 = razones de no asistencia; 69..79 = cada razón)
        Pantalla("salud", (11, 56, 57, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 58, 59)),
        # seguimientoEmpleoOtros.js
        Pantalla(
            "empleo",
            (37, 38, 40, 41, 39, 31, 12, 20, 21),
            especiales={
                (31, "odei-mes"): _nini,
                **{(36, v): _etnicidad(v) for v in VISTAS},
                (42, "trimestral"): lambda f: [
                    Llamada(
                        procedimiento(42, "departamentos"),
                        [todos(f["sede"], "0"), todos(f["usuario"], "0")],
                    )  # fmt: skip
                ],
                (42, "pet"): _pet,
                (42, "encuestadores"): lambda f: [
                    Llamada(ENCUESTADORES, [todos(f["sede"], "0"), f["_usuario"]])
                ],
            },
            procedimientos=(
                *(procedimiento(31, "odei-mes", f"_{g}") for g in NINI),
                *(procedimiento(36, v) for v in VISTAS),
                procedimiento(42, "departamentos"),
                PET_ANUAL,
                PET_MENSUAL,
                ENCUESTADORES,
            ),
        ),
    )
}


for _p in PANTALLAS.values():
    sistema_actual.registrar_procedimientos(
        *(procedimiento(i, v) for i in _p.indicadores for v in VISTAS), *_p.procedimientos
    )


def obtener(pantalla: str, vista: str, indicador: int) -> Callable[[dict], list[Llamada]]:
    """Las llamadas que corresponden a la pantalla, vista e indicador (o 404)."""
    p = PANTALLAS.get(pantalla)
    if p is None:
        raise NotFound(f"La pantalla '{pantalla}' no existe.")
    if not p.acepta(indicador):
        raise NotFound(f"El indicador {indicador} no pertenece a '{pantalla}'.")
    if (indicador, vista) in p.especiales:
        return p.especiales[(indicador, vista)]
    if indicador in p.indicadores and vista in VISTAS:
        return lambda f: [Llamada(procedimiento(indicador, vista), parametros_estandar(vista, f))]
    raise NotFound(f"La vista '{vista}' no existe para el indicador {indicador}.")
