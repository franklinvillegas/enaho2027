"""Consulta de los indicadores de calidad (y sus datos de demostración)."""

import random
from datetime import date

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.comun import sistema_actual
from apps.comun.constantes import ODEI_NACIONAL, ODEIS

from .indicadores import obtener, procedimiento


class FiltrosCalidadSerializer(serializers.Serializer):
    indicador = serializers.IntegerField(min_value=1, max_value=999)
    sede = serializers.RegexField(r"^\d{1,2}(\.\d)?$", default="0")
    usuario = serializers.RegexField(r"^[0-9A-Za-z_]{1,20}$", default="0")
    conglomerado = serializers.RegexField(r"^(0|\d{6})$", default="0")
    mes_inicio = serializers.IntegerField(min_value=0, max_value=12, default=0)
    mes_fin = serializers.IntegerField(min_value=0, max_value=12, default=0)
    periodo_inicio = serializers.IntegerField(min_value=0, max_value=5, default=0)
    periodo_fin = serializers.IntegerField(min_value=0, max_value=5, default=0)
    excluir = serializers.ChoiceField(choices=[0, 1, 2, 3], default=0)
    # "Visualizar casos": ODEI del combo (0 = todas)
    odei = serializers.RegexField(r"^\d{1,2}$", default="0")

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


def verificar_alcance(filtros: dict, usuario) -> None:
    """Igual que validarOdei() de la pantalla actual: un usuario de ODEI solo ve la suya."""
    if not usuario.odei or usuario.odei == ODEI_NACIONAL:
        return
    for campo in ("sede", "odei"):
        sede = str(filtros[campo]).split(".")[0]
        if sede not in ("0", "00") and int(sede) != int(usuario.odei):
            raise PermissionDenied("Solo puede consultar el detalle de su ODEI.")


def _mes(m: int) -> str:
    # La pantalla actual manda "0" cuando no se eligió mes y "01".."12" si se eligió
    return f"{m:02d}" if m else "0"


def _todos(valor: str, vacio: str) -> str:
    return vacio if str(valor) in ("0", "00", "") else str(valor)


def parametros(vista: str, f: dict, tipo_casos: int = 0) -> list[str]:
    sede = _todos(f["sede"], "0")
    usuario = _todos(f["usuario"], "")
    if vista == "departamentos":
        return []
    if vista == "odei":
        return [sede, usuario]
    rango = [str(f["periodo_inicio"]), str(f["periodo_fin"]), _mes(f["mes_inicio"]),
             _mes(f["mes_fin"])]  # fmt: skip
    if vista == "odei-mes":
        return [sede, usuario, f["conglomerado"], *rango, str(f["excluir"])]
    # casos (detalleBalanceHogar): odei, tipo, periodo inicial y final, mes inicial y final
    return [_todos(f["odei"], "0"), str(tipo_casos), *rango]


def consultar(pantalla: str, vista: str, f: dict) -> list[dict]:
    p = obtener(pantalla, vista, f["indicador"])
    if settings.FUENTE_COBERTURA == "demo":
        return demo(vista, f)
    if vista == "casos":
        return sistema_actual.ejecutar_procedimiento(
            p.procedimiento_casos, parametros(vista, f, p.casos[f["indicador"]])
        )
    return sistema_actual.ejecutar_procedimiento(
        procedimiento(f["indicador"], vista), parametros(vista, f)
    )


# ---------------------------------------------------------------------------------------
# Demostración (FUENTE_COBERTURA=demo): mismas columnas que devuelven los procedimientos
# ---------------------------------------------------------------------------------------

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "setiembre", "octubre", "noviembre", "diciembre"]  # fmt: skip
_DEPARTAMENTOS = ["AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
                  "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD",
                  "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA",
                  "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"]  # fmt: skip


def demo(vista: str, f: dict) -> list[dict]:
    r = random.Random(f"cal-{vista}-{f['indicador']}-{f['sede']}-{f['usuario']}")
    anio = date.today().year
    base = 2.5 if f["indicador"] == 1 else r.uniform(5, 90)

    def v():
        return round(max(0.0, base + r.uniform(-base * 0.2, base * 0.2)), 2)

    if vista == "casos":
        return [
            {"id": k, "año": anio, "odei": "14", "nomodei": "LAMBAYEQUE",
             "mes": f"{r.randint(1, 12):02d}", "periodo": r.randint(1, 5),
             "conglome": f"{r.randint(1, 999999):06d}", "vivienda": f"{r.randint(1, 140):03d}",
             "hogar": "11", "result": 1, "ingreso_total": round(r.uniform(800, 5000), 2),
             **{f"ingreso0{n}": round(r.uniform(0, 900), 2) for n in range(1, 6)},
             "ingreso_trabajo": round(r.uniform(0, 3000), 2),
             "alquiler_imputado": round(r.uniform(0, 600), 2),
             "gasto_total": round(r.uniform(800, 6000), 2),
             **{f"gasto0{n}": round(r.uniform(0, 900), 2) for n in range(1, 9)},
             "gasto_alimentosbebidas": round(r.uniform(200, 1500), 2),
             "gasto_alimentosdentrohogar": round(r.uniform(100, 900), 2),
             "codencue": f"{40000000 + k}", "nomencue": f"ENCUESTADOR {k:02d}",
             "balance": round(r.uniform(-80, -20), 1)}
            for k in range(1, 21)
        ]  # fmt: skip

    def datos():
        if vista == "odei-mes":
            fila = {}
            for suf in ("Anterior2", "Anterior", "Actual"):
                fila[f"indicador{suf}"] = v()
                for m in _MESES:
                    fila[f"{m}{suf}"] = v()
            return fila
        fila = {f"indicador{a}": v() for a in range(2013, anio + 1)}
        fila["Estado"] = r.choice(["Aceptable", "Revisar"])
        return fila

    sede, usuario = _todos(f["sede"], "0"), _todos(f["usuario"], "0")
    if vista == "departamentos":
        nombres = ["NACIONAL", "URBANO", "RURAL", *_DEPARTAMENTOS]
        return [{"id": k, "idMostrar": k, "nombreMostrar": n, **datos()}
                for k, n in enumerate(nombres)]  # fmt: skip
    if sede == "0":
        return [{"id": 0, "idMostrar": 0, "nombreMostrar": "NACIONAL", **datos()}] + [
            {"id": k, "idMostrar": c, "nombreMostrar": n, **datos()}
            for k, (c, n) in enumerate(ODEIS[1:], 1)
        ]
    nombre_sede = dict(ODEIS).get(sede.zfill(2), f"SEDE {sede}")
    if usuario == "0":
        return [{"id": 0, "idMostrar": 0, "nombreMostrar": nombre_sede, "encuestador": "TOTAL",
                 **datos()}] + [
            {"id": k, "nombreMostrar": nombre_sede, "usuario": f"{10000000 + k}",
             "encuestador": f"ENCUESTADOR {k:02d}", **datos()}
            for k in range(1, 9)
        ]  # fmt: skip
    if f["conglomerado"] == "0":
        return [{"id": 0, "nombreMostrar": nombre_sede, "encuestador": "ENCUESTADOR",
                 "conglomerado": "TOTAL", **datos()}] + [
            {"id": k, "nombreMostrar": nombre_sede, "encuestador": "ENCUESTADOR",
             "conglomerado": f"{r.randint(1, 999999):06d}", "mes": f"{r.randint(1, 12):02d}",
             **datos()}
            for k in range(1, 9)
        ]  # fmt: skip
    return [{"id": 0, **datos()}] + [
        {"id": k, "mes": f"{r.randint(1, 12):02d}", "conglomerado": f["conglomerado"],
         "vivienda": f"{k:03d}", "hogar": "11", **datos()}
        for k in range(1, 7)
    ]  # fmt: skip
