"""Tasa de no respuesta según estrato socioeconómico (solo área urbana).

Pantalla actual: templates/.../tasaNoRespuesta/tnr_estrato.html + static/.../tnr_estrato.js.
Procedimientos y orden de parámetros tomados de consultasdb/api/views.py
(sp_tnr_estrato, sp_tnr_estrato_mes y sp_tnr_estrato_hogar).

A diferencia de la TNR total y parcial, esta pantalla tiene cuatro pestañas:
  - RESUMEN GRÁFICO: barras por estrato (A..E) y año, para total urbano, Lima
    Metropolitana y resto urbano (de los datos anuales del nivel nacional).
  - RESUMEN ESTRATO (anual): nacional > estrato > ODEI > conglomerados.
  - RESUMEN POR MES: nacional > estrato > ODEI > conglomerado > viviendas.
  - RESUMEN TABULAR: hogares de una ODEI y mes.

Parámetros como los envía la pantalla actual:
  - tipo: 0 nacional, 1 total urbano, 2 Lima Metropolitana, 3 resto urbano
  - estrato: 0 todos, 1 (A, más alto) .. 5 (E, más bajo)
  - odei: "00" todas; conglomerado: "0" todos
  - meses "01".."12" ("00" sin filtro), periodos 0..5, excluir 0..3
"""

import random
from datetime import date

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.comun import sistema_actual
from apps.comun.constantes import ODEI_NACIONAL, ODEIS

from .tasas_no_respuesta import mes

TITULO = "TNR SEGÚN ESTRATO"
TITULOS = {
    "anual": "TNR SEGÚN ESTRATO POR ODEI ANUAL",
    "mensual": "TNR SEGÚN ESTRATO POR ODEI Y POR MES",
    "hogar": "TNR SEGÚN ESTRATO POR HOGAR",
}
AREAS = {1: "TOTAL URBANO", 2: "LIMA METROPOLITANA", 3: "RESTO URBANO"}
ESTRATOS = {1: "A (mas alto)", 2: "B", 3: "C", 4: "D", 5: "E (mas bajo)"}
EXCLUSIONES = {
    0: "Sin exclusiones",
    1: "Excluir no panel",
    2: "Excluir panel",
    3: "Excluir panel con resultado ausente y subresultado no tiene teléfono",
}

PROC_ANUAL = "ENAHO2017_TNR_ESTRATO_V3"
PROC_MENSUAL = "ENAHO2017_TNR_ESTRATO_MES_V3"
PROC_HOGAR = "ENAHO2017_TNR_ESTRATO_HOGAR"
sistema_actual.registrar_procedimientos(PROC_ANUAL, PROC_MENSUAL, PROC_HOGAR)


class _Rango(serializers.Serializer):
    mes_inicio = serializers.IntegerField(min_value=0, max_value=12, default=0)
    periodo_inicio = serializers.IntegerField(min_value=0, max_value=5, default=0)
    mes_fin = serializers.IntegerField(min_value=0, max_value=12, default=0)
    periodo_fin = serializers.IntegerField(min_value=0, max_value=5, default=0)
    excluir = serializers.ChoiceField(choices=[0, 1, 2, 3], default=0)

    def validate(self, datos):
        # Mismas validaciones que la pantalla actual
        if datos["mes_fin"] and datos["mes_fin"] < datos["mes_inicio"]:
            raise serializers.ValidationError("Seleccione mes final mayor o igual al mes inicial.")
        if bool(datos["periodo_inicio"]) != bool(datos["periodo_fin"]):
            raise serializers.ValidationError("Seleccione periodo inicial y final.")
        if (
            datos["periodo_fin"]
            and datos["mes_inicio"] == datos["mes_fin"]
            and datos["periodo_inicio"] > datos["periodo_fin"]
        ):
            raise serializers.ValidationError(
                "Seleccione periodo final mayor o igual al periodo inicial."
            )
        return datos


class FiltrosAnualSerializer(_Rango):
    tipo = serializers.ChoiceField(choices=[0, 1, 2, 3], default=0)
    estrato = serializers.IntegerField(min_value=0, max_value=5, default=0)
    odei = serializers.RegexField(r"^\d{1,2}$", default="00")


class FiltrosMensualSerializer(FiltrosAnualSerializer):
    conglomerado = serializers.RegexField(r"^(0|\d{6})$", default="0")


class FiltrosHogarSerializer(serializers.Serializer):
    odei = serializers.IntegerField(min_value=0, max_value=99, default=0)
    mes = serializers.IntegerField(min_value=0, max_value=12, default=0)


def verificar_alcance(odei, usuario) -> None:
    """Igual que validarOdei() de la pantalla actual: un usuario de ODEI solo ve la suya."""
    if not usuario.odei or usuario.odei == ODEI_NACIONAL:
        return
    if int(odei or 0) and int(odei) != int(usuario.odei):
        raise PermissionDenied("Solo puede consultar el detalle de su ODEI.")


def _rango(f) -> list:
    return [mes(f["mes_inicio"]), f["periodo_inicio"], mes(f["mes_fin"]), f["periodo_fin"]]


def consultar_anual(f: dict) -> list[dict]:
    if settings.FUENTE_COBERTURA == "demo":
        return _demo_anual(f)
    parametros = [f["tipo"], f["estrato"], f["odei"], *_rango(f), f["excluir"]]
    return sistema_actual.ejecutar_procedimiento(PROC_ANUAL, [str(p) for p in parametros])


def consultar_mensual(f: dict) -> list[dict]:
    if settings.FUENTE_COBERTURA == "demo":
        return _demo_mensual(f)
    parametros = [f["tipo"], f["estrato"], f["odei"], f["conglomerado"], *_rango(f), f["excluir"]]
    return sistema_actual.ejecutar_procedimiento(PROC_MENSUAL, [str(p) for p in parametros])


def consultar_hogar(f: dict) -> list[dict]:
    if settings.FUENTE_COBERTURA == "demo":
        return _demo_hogar(f)
    return sistema_actual.ejecutar_procedimiento(PROC_HOGAR, [str(f["odei"]), str(f["mes"])])


def nombre_odei(codigo) -> str:
    return dict((int(c), n) for c, n in ODEIS).get(int(codigo or 0), "")


def info() -> dict:
    return {
        "titulo": TITULO,
        "titulos": TITULOS,
        "areas": {str(k): v for k, v in AREAS.items()},
        "estratos": {str(k): v for k, v in ESTRATOS.items()},
        "exclusiones": [{"valor": k, "nombre": v} for k, v in EXCLUSIONES.items()],
        "odeis": [{"codigo": c, "nombre": n} for c, n in ODEIS if c != ODEI_NACIONAL],
    }


# ---------------------------------------------------------------------------------------
# Modo demo: filas INVENTADAS con las mismas columnas que los procedimientos actuales.
# ---------------------------------------------------------------------------------------


def _filas_area(r: random.Random, datos) -> list[dict]:
    """ORDEN 0/6/12 = área (total urbano, Lima Metropolitana, resto urbano); 1-5 estratos."""
    filas = []
    for k, (tipo, area) in enumerate(AREAS.items()):
        filas.append({"ORDEN": k * 6, "NOMBAREA": area, "ESTRATO": 0, **datos()})
        for e in ESTRATOS:
            filas.append({"ORDEN": k * 6 + e, "NOMBAREA": area, "ESTRATO": e, "TIPO": tipo,
                          **datos()})  # fmt: skip
    return filas


def _demo_anual(f) -> list[dict]:
    r = random.Random(f"estrato-anual-{f['tipo']}-{f['estrato']}-{f['odei']}")

    def datos():
        fila = {}
        for a in range(2017, date.today().year + 1):
            p_abs, np_abs = r.randint(5, 300), r.randint(5, 300)
            fila |= {f"TNR{a}": round(r.uniform(2, 15), 1), f"TNR{a}P": round(r.uniform(2, 15), 1),
                     f"TNR{a}P_ABS": p_abs, f"TNR{a}NP": round(r.uniform(2, 15), 1),
                     f"TNR{a}NP_ABS": np_abs}  # fmt: skip
        return fila

    if f["tipo"] == 0:
        return _filas_area(r, datos)
    if f["odei"] in ("0", "00"):
        return [
            {"ORDEN": 0, "ODEI": "00", "NOMODEI": "TOTAL", "ESTRATO": f["estrato"], **datos()},
            *[{"ORDEN": k, "ODEI": c, "NOMODEI": n, "ESTRATO": f["estrato"], **datos()}
              for k, (c, n) in enumerate(ODEIS[1:], 1)],
        ]  # fmt: skip
    return [
        {"ORDEN": 0, "CONGLOME": "TOTAL", **datos()},
        *[{"ORDEN": k, "CONGLOME": f"{r.randint(1, 999999):06d}", **datos()} for k in range(1, 9)],
    ]


def _demo_mensual(f) -> list[dict]:
    r = random.Random(f"estrato-mes-{f['tipo']}-{f['estrato']}-{f['odei']}-{f['conglomerado']}")

    def datos():
        fila = {"TNR": round(r.uniform(2, 15), 1)}
        for g in ("P", "NP"):
            fila[f"TNR{g}"] = round(r.uniform(2, 15), 1)
            fila[f"TNR{g}_ABS"] = r.randint(5, 300)
            for m in range(1, 13):
                fila[f"TNR{g}_{m}"] = round(r.uniform(0, 20), 1)
                fila[f"TNR{g}_{m}_ABS"] = r.randint(0, 40)
        return fila

    if f["tipo"] == 0:
        return _filas_area(r, datos)
    if f["odei"] in ("0", "00"):
        return [
            {"ORDEN": 0, "ODEI": "00", "NOMODEI": "TOTAL", "ESTRATO": f["estrato"], **datos()},
            *[{"ORDEN": k, "ODEI": c, "NOMODEI": n, "ESTRATO": f["estrato"], **datos()}
              for k, (c, n) in enumerate(ODEIS[1:], 1)],
        ]  # fmt: skip
    if f["conglomerado"] == "0":
        return [
            {"ORDEN": 0, "CONGLOME": "TOTAL", "ESTRATO": f["estrato"], **datos()},
            *[{"ORDEN": k, "CONGLOME": f"{r.randint(1, 999999):06d}", "ODEI": f["odei"],
               "ESTRATO": f["estrato"], **datos()} for k in range(1, 9)],
        ]  # fmt: skip
    return [
        {"ORDEN": 0, "CONGLOME": f["conglomerado"], **datos()},
        *[{"ORDEN": k, "VIVIENDA": f"{k:03d}", **datos()} for k in range(1, 9)],
    ]


def _demo_hogar(f) -> list[dict]:
    r = random.Random(f"estrato-hogar-{f['odei']}-{f['mes']}")
    odeis = [(c, n) for c, n in ODEIS[1:] if not f["odei"] or int(c) == f["odei"]]
    return [
        {"ID": k, "ANIO": date.today().year, "ODEI": c, "NOMODEI": n, "DISTRITO": "CHICLAYO",
         "NOMAREAGEN": "URBANO", "MES": f"{f['mes'] or r.randint(1, 12):02d}",
         "PERIODO": r.randint(1, 5), "CONGLOME": f"{r.randint(1, 999999):06d}",
         "VIVIENDA": f"{r.randint(1, 120):03d}", "HOGAR": "11", "RESULTADO": r.choice([3, 4]),
         "TIPOVIVIENDA": r.choice(["PANEL", "NO PANEL"]), "ESTRATO": r.randint(1, 5),
         "VIVIENDAS_CONGLOME": r.randint(6, 14), "TNR_CONGLOME": round(r.uniform(5, 40), 1)}
        for k, (c, n) in enumerate([r.choice(odeis) for _ in range(25)], 1)
    ]  # fmt: skip
