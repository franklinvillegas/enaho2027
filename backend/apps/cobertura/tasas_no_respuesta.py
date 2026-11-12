"""Motor común de las pantallas de tasa de no respuesta (total, parcial, ...).

En el sistema actual cada pantalla (tnr_total.js, tnr_parcial.js) repetía ~2.500 líneas
casi idénticas: mismas tres vistas, mismas pestañas, misma profundización
(nacional > sede > encuestador > conglomerado) y mismo Excel. Solo cambiaban los
procedimientos, el prefijo de las columnas (tnr2026 / tnrp_2026), los textos y los
filtros extra. Aquí cada pantalla es una configuración (IndicadorTnr) y el resto es común.

Formato de los parámetros igual al que envían las pantallas actuales:
  - meses "01".."12" ("00" = sin filtro), periodos 0..5 (0 = todos)
  - sede: código de ODEI tal como lo devuelve el procedimiento en idMostrar ("15", "15.1")
  - usuario: DNI o usuario del encuestador
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.comun import sistema_actual
from apps.comun.constantes import ODEI_NACIONAL

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "setiembre", "octubre", "noviembre", "diciembre"]  # fmt: skip


def mes(valor) -> str:
    return f"{int(valor or 0):02d}"


def rango(f) -> list:
    return [f["periodo_inicio"], f["periodo_fin"], mes(f["mes_inicio"]), mes(f["mes_fin"])]


@dataclass(frozen=True)
class Vista:
    nombre: str
    procedimiento: str
    parametros: Callable[[dict], list]


@dataclass(frozen=True)
class IndicadorTnr:
    """Configuración de una pantalla de tasa de no respuesta."""

    codigo: str  # tnr-total
    titulo: str  # Tasa de no respuesta total
    titulo_excel: str  # TNR TOTAL
    descripcion: str
    formula: str
    vistas: dict[str, Vista]
    procedimiento_mapa: str
    # Columnas por año: tnr2026 (total) o tnrp_2026 (parcial)
    prefijo: str
    # Filtros que solo tiene esta pantalla: "excluir", "solo_activos"
    filtros_extra: tuple[str, ...] = ()
    # Escala azul en la última columna de años (solo TNR total)
    colorear_ultimo: bool = False
    # Textos y colores de los gráficos, iguales a la pantalla actual
    grafico: dict = field(default_factory=dict)
    # Encabezado en vez de "AÑOS" en el detalle de un conglomerado (nivel 4)
    titulo_detalle: str = "AÑOS"
    # Encabezado de las columnas en la vista por mes (información indirecta lo cambia)
    titulo_meses: str = "AÑOS"
    # Tabla extra de valores absolutos por encuestador, debajo de la tabla de una sede en
    # la vista por ODEI y mes (solo información indirecta)
    absolutos: Vista | None = None
    # Título de la pantalla si no es el título en mayúsculas ("INFORMACIÓN INDIRECTA")
    titulo_pantalla: str = ""

    @property
    def procedimientos(self) -> list[str]:
        extra = [self.absolutos.procedimiento] if self.absolutos else []
        return [self.procedimiento_mapa, *(v.procedimiento for v in self.vistas.values()), *extra]

    def info(self) -> dict:
        """Lo que la pantalla necesita para dibujarse (títulos, vistas, gráficos)."""
        return {
            "codigo": self.codigo,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "formula": self.formula,
            "prefijo": self.prefijo,
            "filtros_extra": list(self.filtros_extra),
            "colorear_ultimo": self.colorear_ultimo,
            "titulo_detalle": self.titulo_detalle,
            "titulo_meses": self.titulo_meses,
            "titulo_pantalla": self.titulo_pantalla or self.titulo.upper(),
            "absolutos": self.absolutos.nombre if self.absolutos else None,
            "grafico": self.grafico,
            "vistas": [{"codigo": k, "nombre": v.nombre} for k, v in self.vistas.items()],
        }


REGISTRO: dict[str, IndicadorTnr] = {}


def registrar(indicador: IndicadorTnr) -> IndicadorTnr:
    REGISTRO[indicador.codigo] = indicador
    sistema_actual.registrar_procedimientos(*indicador.procedimientos)
    return indicador


def obtener(codigo: str) -> IndicadorTnr:
    try:
        return REGISTRO[codigo]
    except KeyError:
        raise NotFound(f"Indicador '{codigo}' no existe.") from None


class FiltrosTnrSerializer(serializers.Serializer):
    periodo_inicio = serializers.IntegerField(min_value=0, max_value=5, default=0)
    periodo_fin = serializers.IntegerField(min_value=0, max_value=5, default=0)
    mes_inicio = serializers.IntegerField(min_value=0, max_value=12, default=0)
    mes_fin = serializers.IntegerField(min_value=0, max_value=12, default=0)
    sede = serializers.RegexField(r"^\d{1,2}(\.\d)?$", default="0")
    usuario = serializers.RegexField(r"^[0-9A-Za-z_]{1,20}$", default="0")
    conglomerado = serializers.RegexField(r"^(0|\d{6})$", default="0")
    solo_activos = serializers.BooleanField(default=False)
    excluir = serializers.ChoiceField(choices=[0, 1, 2, 3], default=0)

    def validate(self, datos):
        if datos["mes_fin"] and datos["mes_fin"] < datos["mes_inicio"]:
            raise serializers.ValidationError({"mes_fin": "El mes final es anterior al inicial."})
        if (
            datos["periodo_fin"]
            and datos["mes_inicio"] == datos["mes_fin"]
            and datos["periodo_inicio"] > datos["periodo_fin"]
        ):
            raise serializers.ValidationError(
                {"periodo_fin": "El periodo final es anterior al inicial."}
            )
        return datos


def _misma_odei(sede: str, odei_usuario: str) -> bool:
    return sede.split(".")[0].lstrip("0") == (odei_usuario or "").lstrip("0")


def verificar_alcance(filtros: dict, usuario) -> None:
    """Un usuario de una ODEI ve el resumen nacional, pero solo profundiza en su ODEI."""
    if not usuario.odei or usuario.odei == ODEI_NACIONAL:
        return
    if filtros["sede"] != "0" and not _misma_odei(filtros["sede"], usuario.odei):
        raise PermissionDenied("Solo puede consultar el detalle de su ODEI.")


def consultar(indicador: IndicadorTnr, vista: str, filtros: dict) -> list[dict]:
    try:
        config = indicador.vistas[vista]
    except KeyError:
        raise NotFound(f"Vista '{vista}' no existe.") from None
    if settings.FUENTE_COBERTURA == "demo":
        return demo(indicador, vista, filtros)
    parametros = [str(p) for p in config.parametros(filtros)]
    return sistema_actual.ejecutar_procedimiento(config.procedimiento, parametros)


def consultar_absolutos(indicador: IndicadorTnr, filtros: dict) -> list[dict]:
    if not indicador.absolutos:
        raise NotFound("Esta pantalla no tiene tabla de valores absolutos.")
    if settings.FUENTE_COBERTURA == "demo":
        return demo_absolutos(filtros)
    parametros = [str(p) for p in indicador.absolutos.parametros(filtros)]
    return sistema_actual.ejecutar_procedimiento(indicador.absolutos.procedimiento, parametros)


def consultar_mapa(indicador: IndicadorTnr) -> list[dict]:
    if settings.FUENTE_COBERTURA == "demo":
        return demo_mapa(indicador)
    return sistema_actual.ejecutar_procedimiento(indicador.procedimiento_mapa)


# ---------------------------------------------------------------------------------------
# Modo demo: filas INVENTADAS con la misma forma que devuelven los procedimientos actuales,
# para trabajar las pantallas sin acceso a la base. Solo con FUENTE_COBERTURA=demo.
# ---------------------------------------------------------------------------------------

_SEDES = ["AMAZONAS", "ANCASH-HUARAZ", "ANCASH-CHIMBOTE", "APURIMAC", "AREQUIPA",
          "AYACUCHO", "CAJAMARCA", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN",
          "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "PIURA", "PUNO", "SAN MARTIN",
          "TACNA", "UCAYALI"]  # fmt: skip


def demo(indicador: IndicadorTnr, vista: str, filtros: dict) -> list[dict]:
    p = indicador.prefijo
    anio = date.today().year
    con_abs = indicador.codigo == "tnr-parcial"  # en la parcial cada año trae su absoluto
    abs_mes = indicador.codigo != "problemas-marco"  # problemas de marco no trae absolutos
    r = random.Random(f"{indicador.codigo}-{vista}-{filtros['sede']}-{filtros['usuario']}")

    def anios():
        fila = {}
        for a in range(2013, anio + 1):
            fila[f"{p}{a}"] = round(r.uniform(4, 11), 1)
            if con_abs:
                fila[f"{p}{a}_abs"] = r.randint(50, 2000)
        return fila

    def meses(solo_actual=False):
        fila = {}
        for a in (anio,) if solo_actual else (anio - 1, anio):
            fila[f"{p}{a}"] = round(r.uniform(4, 9), 1)
            if abs_mes:
                fila[f"{p}{a}_abs"] = r.randint(80, 2000)
            for m in MESES:
                fila[f"{m}_{a}"] = round(r.uniform(0, 12), 1)
                if abs_mes:
                    fila[f"{m}_{a}_abs"] = r.randint(0, 200)
        return fila

    if vista == "departamentos":
        nombres = [("NACIONAL", ""), ("URBANO", 1), ("RURAL", 2), ("AMBITO GEOGRAFICO", 0),
                   ("LIMA METROPOLITANA", 1), ("RESTO URBANO", 2), ("RURAL", 3)]  # fmt: skip
        return [
            {"idMostrar": i, "nombreMostrar": n, **anios()}
            if i != 0
            else {"idMostrar": 0, "nombreMostrar": n, **dict.fromkeys(anios(), None)}
            for n, i in nombres
        ]
    por_mes = vista == "odei-mes"
    if filtros["conglomerado"] != "0":
        return [
            {"id": 0, f"{p}{anio}": round(r.uniform(4, 9), 1)},
            *[
                {
                    "id": k,
                    "mes": f"{r.randint(1, 12):02d}",
                    "conglomerado": filtros["conglomerado"],
                    "vivienda": f"{k:03d}",
                    "hogar": "11",
                    f"{p}{anio}": r.choice([0, 100]),
                }
                for k in range(1, 9)
            ],  # fmt: skip
        ]
    if filtros["usuario"] != "0":
        return [
            {"id": 0, "idMostrar": 0, "encuestador": "TOTAL", "conglomerado": "",
             **(meses(solo_actual=True) if por_mes else anios())},
            *[
                {"id": k, "idMostrar": k, "conglomerado": f"{r.randint(1, 999999):06d}",
                 "mes": f"{r.randint(1, 12):02d}", "tipEnc": "01", "viv": r.randint(5, 15),
                 **(meses(solo_actual=True) if por_mes else anios())}
                for k in range(1, 9)
            ],
        ]  # fmt: skip
    datos = meses if por_mes else anios
    if filtros["sede"] != "0":
        return [
            {"id": 0, "idMostrar": 0, "nombreMostrar": "TOTAL SEDE", "encuestador": "TOTAL",
             **datos()},
            *[
                {"id": k, "idMostrar": k, "usuario": f"{10000000 + k}",
                 "encuestador": f"ENCUESTADOR {k:02d}", "activo": 1, **datos()}
                for k in range(1, 11)
            ],
        ]  # fmt: skip
    return [
        {"idMostrar": 0, "nombreMostrar": "NACIONAL", **datos()},
        *[{"idMostrar": k, "nombreMostrar": s, **datos()} for k, s in enumerate(_SEDES, 1)],
    ]


def demo_mapa(indicador: IndicadorTnr) -> list[dict]:
    r = random.Random(f"mapa-{indicador.codigo}")
    deps = ["AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA", "CALLAO",
            "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD", "LAMBAYEQUE",
            "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA", "PUNO",
            "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"]  # fmt: skip
    return [{"departamento": d, "indicador": round(r.uniform(1, 15), 1)} for d in deps]


MESES_ABS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"]


def demo_absolutos(filtros: dict) -> list[dict]:
    """Valores absolutos por encuestador (información indirecta), inventados."""
    r = random.Random(f"abs-{filtros['sede']}")
    anio = date.today().year
    filas = []
    for k in range(1, 11):
        fila = {"nomencue": f"ENCUESTADOR {k:02d}", "activo": r.choice(["SI", "NO"])}
        for a in (anio - 1, anio):
            fila[f"indirecta{a}"] = r.randint(0, 40)
            fila[f"tot{a}"] = r.randint(100, 400)
            for m, nombre in enumerate(MESES_ABS, 1):
                fila[f"ind_{nombre}{a}"] = r.randint(0, 5)
                fila[f"tot{a}_{m}"] = r.randint(5, 40)
        filas.append(fila)
    return filas
