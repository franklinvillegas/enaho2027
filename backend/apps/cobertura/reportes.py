"""Pantallas de cobertura con estructura propia (no siguen el esquema de la TNR):
control de visitas, omisión por capítulos, omisiones GPS y tipo de entrevista.

Cada pantalla define sus vistas: qué procedimiento llama cada una y con qué parámetros,
en el mismo orden que la pantalla actual (consultasdb/api/views.py). El dibujo de la
tabla y los gráficos lo hace el frontend (config/reportesCobertura/*.js), porque cada
pantalla tiene columnas distintas.

Parámetros comunes (formato de la pantalla actual):
  sede "0"/"00" = todas · usuario/encuestador "0"/"00" = todos · conglomerado "0" = todos
  meses "01".."12" ("00" = sin filtro) · periodos 0..5 · excluir 0..3
"""

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.comun import sistema_actual
from apps.comun.constantes import ODEI_NACIONAL, ODEIS

from .tasas_no_respuesta import mes


@dataclass(frozen=True)
class Consulta:
    procedimiento: str
    parametros: Callable[[dict], list]


class FiltrosReporteSerializer(serializers.Serializer):
    sede = serializers.RegexField(r"^\d{1,2}(\.\d)?$", default="0")
    usuario = serializers.RegexField(r"^[0-9A-Za-z_]{1,20}$", default="0")
    conglomerado = serializers.RegexField(r"^(0|\d{6})$", default="0")
    mes_inicio = serializers.IntegerField(min_value=0, max_value=12, default=0)
    mes_fin = serializers.IntegerField(min_value=0, max_value=12, default=0)
    periodo_inicio = serializers.IntegerField(min_value=0, max_value=5, default=0)
    periodo_fin = serializers.IntegerField(min_value=0, max_value=5, default=0)
    excluir = serializers.ChoiceField(choices=[0, 1, 2, 3], default=0)
    # Filtros de un solo mes y periodo (omisiones GPS)
    mes = serializers.IntegerField(min_value=0, max_value=12, default=0)
    periodo = serializers.IntegerField(min_value=0, max_value=5, default=0)

    def validate(self, datos):
        if datos["mes_fin"] and datos["mes_fin"] < datos["mes_inicio"]:
            raise serializers.ValidationError("Seleccione mes final mayor o igual al mes inicial.")
        if (
            datos["periodo_fin"]
            and datos["mes_inicio"] == datos["mes_fin"]
            and datos["periodo_inicio"] > datos["periodo_fin"]
        ):
            raise serializers.ValidationError(
                "Seleccione periodo final mayor o igual al periodo inicial."
            )
        return datos


def _cero(valor, vacio="0"):
    """Sede o encuestador "todos": la pantalla actual usa "0" o "00" según el procedimiento."""
    return vacio if str(valor) in ("0", "00") else str(valor)


def _rango_pi_pf_mi_mf(f):
    return [f["periodo_inicio"], f["periodo_fin"], mes(f["mes_inicio"]), mes(f["mes_fin"])]


# ---------------------------------------------------------------------------------------
# Pantallas
# ---------------------------------------------------------------------------------------

PANTALLAS: dict[str, dict[str, Consulta]] = {
    # control_visita.js — tipo 1 a 4
    "control-visitas": {
        "departamentos": Consulta("cobertura_controlVisitas_dep", _rango_pi_pf_mi_mf),
        "odei": Consulta(
            "enaho2016_visitas_odei_anio",
            lambda f: [_cero(f["sede"]), _cero(f["usuario"], "00")],
        ),
        "odei-mes": Consulta(
            "enaho2016_visitas_odei_mes",
            lambda f: [
                _cero(f["sede"]),
                _cero(f["usuario"], "00"),
                *_rango_pi_pf_mi_mf(f),
                f["excluir"],
            ],  # fmt: skip
        ),
        "casos": Consulta(
            "cobertura_controlVisitas_casos",
            lambda f: [_cero(f["sede"]), *_rango_pi_pf_mi_mf(f)],
        ),
    },
    # omision_capitulo.js — gráfico, tabla por año, tabla por mes y mapa
    "omision-capitulos": {
        "grafico": Consulta(
            "enaho2015_calidad_ind02", lambda f: [_cero(f["sede"], "00"), _cero(f["usuario"])]
        ),
        "anio": Consulta(
            "ENAHO2020_CALIDAD_OMISIONCAPITULOS_ANIO",
            lambda f: [_cero(f["sede"], "00"), _cero(f["usuario"])],
        ),
        "mes": Consulta(
            "ENAHO2020_CALIDAD_OMISIONCAPITULOS_MES",
            lambda f: [
                _cero(f["sede"], "00"),
                _cero(f["usuario"]),
                f["conglomerado"],
                *_rango_pi_pf_mi_mf(f),
            ],  # fmt: skip
        ),
        "mapa": Consulta("enaho2015_omision_capitulo_map", lambda f: []),
    },
    # reporte_omisiones.js — % de viviendas sin GPS; el detalle de un conglomerado
    # usa el procedimiento de programado vs. ejecutado (con el año en curso)
    "omisiones-gps": {
        "resumen": Consulta(
            "enaho2016_geo_omisiones",
            lambda f: [
                _cero(f["sede"], "00"),
                _cero(f["usuario"]),
                f"{f['mes']:02d}",
                f["periodo"],
            ],
        ),
        "viviendas": Consulta(
            "enaho2015_cobertura_ind01_2",
            # La pantalla actual armaba mal esta llamada (sin el año): aquí va completa
            lambda f: [
                date.today().year,
                _cero(f["sede"]),
                f["conglomerado"],
                f"{f['mes']:02d}",
                f["periodo"],
            ],  # fmt: skip
        ),
    },
    # tipo_entrevista.js — reporte 1 (departamentos), 2 (ODEI) y 3 (ODEI y mes)
    "tipo-entrevista": {
        "departamentos": Consulta("cobertura_tipoEntrevista_dep", _rango_pi_pf_mi_mf),
        "odei": Consulta(
            "enaho2021_tipoEntrevista_odei",
            lambda f: [_cero(f["sede"]), _cero(f["usuario"]), f["conglomerado"]],
        ),
        "odei-mes": Consulta(
            "enaho2021_tipoEntrevista_odeiMes",
            lambda f: [_cero(f["sede"]), _cero(f["usuario"]), f["conglomerado"]],
        ),
    },
}

for _vistas in PANTALLAS.values():
    sistema_actual.registrar_procedimientos(*(c.procedimiento for c in _vistas.values()))


def obtener(pantalla: str, vista: str) -> Consulta:
    try:
        return PANTALLAS[pantalla][vista]
    except KeyError:
        raise NotFound(f"Reporte '{pantalla}/{vista}' no existe.") from None


def verificar_alcance(filtros: dict, usuario) -> None:
    """Igual que validarOdei() de la pantalla actual: un usuario de ODEI solo ve la suya."""
    if not usuario.odei or usuario.odei == ODEI_NACIONAL:
        return
    sede = str(filtros["sede"]).split(".")[0]
    if sede not in ("0", "00") and int(sede) != int(usuario.odei):
        raise PermissionDenied("Solo puede consultar el detalle de su ODEI.")


def consultar(pantalla: str, vista: str, filtros: dict) -> list[dict]:
    consulta = obtener(pantalla, vista)
    if settings.FUENTE_COBERTURA == "demo":
        return DEMOS[pantalla](vista, filtros)
    parametros = [str(p) for p in consulta.parametros(filtros)]
    return sistema_actual.ejecutar_procedimiento(consulta.procedimiento, parametros)


# ---------------------------------------------------------------------------------------
# Modo demo: filas INVENTADAS con las mismas columnas que los procedimientos actuales.
# ---------------------------------------------------------------------------------------

_MES3 = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"]
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "setiembre", "octubre", "noviembre", "diciembre"]  # fmt: skip
_CAPITULOS = ["TOTAL", "700", "710", "602M", "602AM", "603M", "604M", "605M", "606M", "606DM",
              "607M", "609M", "610M", "611M", "612M", "GOBER", "CORRUP", "ALIM"]  # fmt: skip


def _nivel(f):
    if _cero(f["sede"]) == "0":
        return 1
    if _cero(f["usuario"]) == "0":
        return 2
    return 3 if f["conglomerado"] == "0" else 4


def _filas_niveles(f, r, datos, nombre_nivel1="NACIONAL"):
    """Filas tipo: total + ODEI / encuestadores / conglomerados según el nivel."""
    n = _nivel(f)
    if n == 1:
        return [{"id": 0, "idMostrar": 0, "cododei": 0, "odei": "0", "codOdei": "00",
                 "nombreMostrar": nombre_nivel1, "nomOdei": nombre_nivel1,
                 "nomodei": nombre_nivel1, **datos()}] + [
            {"id": k, "idMostrar": c, "cododei": c, "odei": c, "codOdei": c, "nombreMostrar": nom,
             "nomOdei": nom, "nomodei": nom, **datos()}
            for k, (c, nom) in enumerate(ODEIS[1:], 1)
        ]  # fmt: skip
    if n == 2:
        return [{"id": 0, "encuestador": "TOTAL", "nomencue": "TOTAL", "nomodei": "SEDE",
                 **datos()}] + [
            {"id": k, "usuario": f"{10000000 + k}", "codencue": f"{10000000 + k}",
             "encuestador": f"ENCUESTADOR {k:02d}", "nomencue": f"ENCUESTADOR {k:02d}",
             "odei": f["sede"], **datos()}
            for k in range(1, 9)
        ]  # fmt: skip
    if n == 3:
        return [{"id": 0, "conglomerado": "", "conglome": "TOTAL", "nomencue": "ENCUESTADOR",
                 **datos()}] + [
            {"id": k, "conglomerado": f"{r.randint(1, 999999):06d}",
             "conglome": f"{r.randint(1, 999999):06d}", "mes": f"{r.randint(1, 12):02d}",
             "odei": f["sede"], "codencue": f["usuario"], **datos()}
            for k in range(1, 9)
        ]  # fmt: skip
    return [{"id": 0, "conglome": f["conglomerado"], **datos()}] + [
        {"id": k, "vivienda": f"{k:03d}", "hogar": "11", **datos()} for k in range(1, 7)
    ]


def _demo_control_visitas(vista, f):
    r = random.Random(f"cv-{vista}-{f['sede']}-{f['usuario']}")
    anio = date.today().year
    if vista == "casos":
        return [
            {"id": k, "anio": anio, "odei": "14", "nomodei": "LAMBAYEQUE",
             "mes": f"{r.randint(1, 12):02d}", "periodo": r.randint(1, 5),
             "conglome": f"{r.randint(1, 999999):06d}", "codencue": f"{40000000 + k}",
             "nomencue": f"ENCUESTADOR {k:02d}", "cantidad_hogares": r.randint(5, 14),
             "cantidad_visitas": r.randint(10, 40), "duracion_visitas": r.randint(200, 900)}
            for k in range(1, 26)
        ]  # fmt: skip

    def anual():
        fila = {}
        for a in range(2013, anio + 1):
            fila[f"promVisitas{a}"] = round(r.uniform(1.1, 2.5), 1)
            fila[f"promDuracion{a}"] = round(r.uniform(40, 90), 1)
        return fila

    def mensual():
        fila = {}
        for suf in ("Anterior2", "Anterior", "Actual"):
            fila[f"promVisitas_{suf}"] = round(r.uniform(1.1, 2.5), 1)
            fila[f"promDuracion_{suf}"] = round(r.uniform(40, 90), 1)
            for m in _MES3:
                fila[f"promVisitas_{m}{suf}"] = round(r.uniform(1.1, 2.5), 1)
                fila[f"promDuracion_{m}{suf}"] = round(r.uniform(40, 90), 1)
        return fila

    if vista == "departamentos":
        nombres = ["NACIONAL", "URBANO", "RURAL", "COSTA", "SIERRA", "SELVA", "LIMA METROPOLITANA"]
        return [{"cododei": k, "nomOdei": n, **anual()} for k, n in enumerate(nombres)]
    filas = _filas_niveles(f, r, anual if vista == "odei" else mensual)
    return filas


def _demo_omision(vista, f):
    r = random.Random(f"om-{vista}-{f['sede']}-{f['usuario']}")
    anio = date.today().year
    if vista == "mapa":
        deps = ["AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA", "CALLAO",
                "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD", "LAMBAYEQUE",
                "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA", "PUNO",
                "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"]  # fmt: skip
        return [{"departamento": d, "indicador": round(r.uniform(1, 12), 1)} for d in deps]
    if vista == "grafico":
        return [{f"a{a}": round(r.uniform(2, 9), 1) for a in range(2013, anio + 1)}]

    def por_anio():
        fila = {}
        for a in range(2013, anio + 1):
            for c in _CAPITULOS:
                fila[f"OMI_{a}_{c}"] = round(r.uniform(0, 6), 1)
                fila[f"OMI_{a}_{c}_ABS"] = r.randint(0, 80)
        return fila

    def por_mes():
        fila = {"OMI_00_TOTAL": round(r.uniform(0, 6), 1), "OMI_00_TOTAL_ABS": r.randint(0, 900)}
        for m in range(1, 13):
            for c in _CAPITULOS:
                fila[f"OMI_{m:02d}_{c}"] = round(r.uniform(0, 6), 1)
                fila[f"OMI_{m:02d}_{c}_ABS"] = r.randint(0, 80)
        return fila

    datos = por_anio if vista == "anio" else por_mes
    filas = _filas_niveles(f, r, datos)
    # Mismas claves que el procedimiento (mayúsculas)
    salida = []
    for fila in filas:
        salida.append({
            "ID": fila.get("id"), "CODODEI": fila.get("odei") or fila.get("codOdei"),
            "ODEI": fila.get("nomodei"), "CODENCUE": fila.get("codencue"),
            "NOMENCUE": fila.get("nomencue"), "CONGLOME": fila.get("conglome"),
            "MES": fila.get("mes"),
            **{k: v for k, v in fila.items() if k.startswith("OMI_")},
        })  # fmt: skip
    return salida


def _demo_gps(vista, f):
    r = random.Random(f"gps-{vista}-{f['sede']}-{f['usuario']}-{f['conglomerado']}")
    if vista == "viviendas":
        return [
            {"conglome": f["conglomerado"], "mes": "05", "dni": f"{40000000 + k}",
             "encuestador": "ENCUESTADOR 01", "VIVIENDA": f"{k:03d}", "totalHogares": 1,
             "hogar": "11", "resultado": 1, "nroReemplazo": 0, "ubigeo": "140101",
             "latitude": -6.77 + r.uniform(-0.01, 0.01),
             "longitude": -79.84 + r.uniform(-0.01, 0.01)}
            for k in range(1, 9)
        ]  # fmt: skip

    def datos():
        meses = {("sep" if m == "set" else m): round(r.uniform(0, 8), 1) for m in _MES3}
        return {"sinGPS": round(r.uniform(0, 5), 1), **meses}

    filas = _filas_niveles(f, r, datos)
    for fila in filas:
        fila.setdefault("codOdei", f["sede"])
        if "conglome" in fila and fila.get("mes"):
            fila["odei"] = fila.get("odei")
    return filas


def _demo_tipo_entrevista(vista, f):
    r = random.Random(f"te-{vista}-{f['sede']}-{f['usuario']}-{f['conglomerado']}")
    anio = date.today().year

    def anual():
        fila = {}
        for a in range(2020, anio + 1):
            pres, telf = r.randint(500, 3000), r.randint(50, 900)
            fila |= {f"entrevPres_{a}": pres, f"entrevTelf_{a}": telf,
                     f"entrevPres_{a}porc": round(100 * pres / (pres + telf), 1),
                     f"entrevTelf_{a}porc": round(100 * telf / (pres + telf), 1)}  # fmt: skip
        return fila

    def mensual():
        fila = {}
        for suf in ("Anterior", "Actual"):
            fila[f"entrevPres_anio{suf}"] = r.randint(500, 3000)
            fila[f"entrevTelf_anio{suf}"] = r.randint(50, 900)
            for m in _MESES:
                fila[f"entrevPres_{m}{suf}"] = r.randint(40, 300)
                fila[f"entrevTelf_{m}{suf}"] = r.randint(0, 80)
        return fila

    if vista == "departamentos":
        nombres = ["NACIONAL", "URBANO", "RURAL", "COSTA", "SIERRA", "SELVA"]
        return [
            {"id": k, "idMostrar": k, "nombreMostrar": n, **anual()} for k, n in enumerate(nombres)
        ]
    return _filas_niveles(f, r, anual if vista == "odei" else mensual)


DEMOS = {
    "control-visitas": _demo_control_visitas,
    "omision-capitulos": _demo_omision,
    "omisiones-gps": _demo_gps,
    "tipo-entrevista": _demo_tipo_entrevista,
}
