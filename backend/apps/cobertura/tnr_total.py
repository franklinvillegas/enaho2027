"""Tasa de no respuesta total: las mismas vistas que la pantalla actual.

Pantalla actual: templates/.../tasaNoRespuesta/tnr_total.html + static/.../tnr_total.js.
Cada botón de la pantalla es una VISTA con su procedimiento. La profundización
(nacional > sede > encuestador > conglomerado) se hace dentro de la vista, llamando al
mismo procedimiento con sede, usuario y conglomerado distintos ("0" = todos).

Formato de los parámetros igual al que envía la pantalla actual:
  - meses "01".."12" ("00" = sin filtro), periodos 0..5 (0 = todos)
  - sede: código de ODEI tal como lo devuelve el procedimiento en idMostrar ("15", "15.1")
  - usuario: DNI o usuario del encuestador
"""

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.comun import sistema_actual
from apps.comun.constantes import ODEI_NACIONAL

TITULO = "Tasa de no respuesta total"

DESCRIPCION = (
    "La Tasa de No Respuesta Total, se define como la proporción de viviendas ocupadas cuyos "
    "informantes no desean ser entrevistados (rechazo) o no están presentes en el momento de "
    "la entrevista. Por lo tanto, este indicador mide la proporción de hogares que no se "
    "entrevistaron entre el total de viviendas ocupadas."
)
FORMULA = (
    "TNR (Neta) = Viv. Resultado 3 y 4 (rechazo y ausente) / "
    "Viv. Resultado 1, 2, 3 y 4 (ocupadas) * 100"
)


def _mes(valor) -> str:
    return f"{int(valor or 0):02d}"


def _rango(f):
    return [f["periodo_inicio"], f["periodo_fin"], _mes(f["mes_inicio"]), _mes(f["mes_fin"])]


VISTAS = {
    "departamentos": {
        "nombre": "Visualizar por Departamentos",
        "procedimiento": "cobertura_tasaNoRespuestaTotal_dep",
        "parametros": _rango,
    },
    "odei": {
        "nombre": "Visualizar por ODEI",
        "procedimiento": "enaho2015_cobertura_ind03_2_v2",
        "parametros": lambda f: [f["sede"], f["usuario"], *_rango(f)],
    },
    "odei-mes": {
        "nombre": "Visualizar por ODEI y por mes",
        "procedimiento": "enaho2015_cobertura_ind03_3_v4",
        "parametros": lambda f: [
            f["sede"],
            f["usuario"],
            f["conglomerado"],
            f["periodo_inicio"],
            f["periodo_fin"],
            1 if f["solo_activos"] else 0,
            _mes(f["mes_inicio"]),
            _mes(f["mes_fin"]),
            f["excluir"],
        ],
    },
}
PROCEDIMIENTO_MAPA = "enaho2015_tnr_total_map"

sistema_actual.registrar_procedimientos(
    PROCEDIMIENTO_MAPA, *(v["procedimiento"] for v in VISTAS.values())
)


class FiltrosTnrTotalSerializer(serializers.Serializer):
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


def consultar(vista: str, filtros: dict) -> list[dict]:
    try:
        config = VISTAS[vista]
    except KeyError:
        raise NotFound(f"Vista '{vista}' no existe.") from None
    if settings.FUENTE_COBERTURA == "demo":
        return _demo(vista, filtros)
    parametros = [str(p) for p in config["parametros"](filtros)]
    return sistema_actual.ejecutar_procedimiento(config["procedimiento"], parametros)


def consultar_mapa() -> list[dict]:
    if settings.FUENTE_COBERTURA == "demo":
        return _demo_mapa()
    return sistema_actual.ejecutar_procedimiento(PROCEDIMIENTO_MAPA)


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "setiembre", "octubre", "noviembre", "diciembre"]  # fmt: skip


def etiqueta_columna(columna: str) -> str:
    """Encabezado legible para el Excel: tnr2026 -> 2026, enero_2026_abs -> Ene 2026 (abs)."""
    fijas = {"idmostrar": "N°", "nombremostrar": "Nombre", "tipenc": "Tipo de encuesta",
             "viv": "Viviendas trabajadas"}  # fmt: skip
    c = columna.lower()
    if c in fijas:
        return fijas[c]
    abs_ = c.endswith("_abs")
    base = c.removesuffix("_abs")
    if base.startswith("tnr") and base[3:].isdigit():
        texto = base[3:]
    elif "_" in base and base.split("_")[0] in MESES:
        mes, anio = base.split("_", 1)
        texto = f"{mes[:3].capitalize()} {anio}"
    else:
        texto = columna.replace("_", " ").capitalize()
    return f"{texto} (abs)" if abs_ else texto


# ---------------------------------------------------------------------------------------
# Modo demo: filas INVENTADAS con la misma forma que devuelven los procedimientos actuales,
# para trabajar la pantalla sin acceso a la base. Solo con FUENTE_COBERTURA=demo.
# ---------------------------------------------------------------------------------------

_SEDES = ["AMAZONAS", "ANCASH-HUARAZ", "ANCASH-CHIMBOTE", "APURIMAC", "AREQUIPA",
          "AYACUCHO", "CAJAMARCA", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN",
          "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "PIURA", "PUNO", "SAN MARTIN",
          "TACNA", "UCAYALI"]  # fmt: skip


def _demo(vista: str, filtros: dict) -> list[dict]:
    import random
    from datetime import date

    anio = date.today().year
    r = random.Random(f"{vista}-{filtros['sede']}-{filtros['usuario']}")

    def anios():
        return {f"tnr{a}": round(r.uniform(4, 11), 1) for a in range(2012, anio + 1)}

    def meses():
        fila = {}
        for a in (anio - 1, anio):
            fila[f"tnr{a}"] = round(r.uniform(4, 9), 1)
            fila[f"tnr{a}_abs"] = r.randint(80, 2000)
            for m in MESES:
                fila[f"{m}_{a}"] = round(r.uniform(0, 12), 1)
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
    datos = meses if vista == "odei-mes" else anios
    if filtros["usuario"] != "0":
        return [
            {"idMostrar": 0, "encuestador": "TOTAL", "conglomerado": "", **datos()},
            *[
                {
                    "idMostrar": k,
                    "conglomerado": f"{r.randint(1, 999999):06d}",
                    "tipEnc": "01",
                    "viv": r.randint(5, 15),
                    **datos(),
                }  # fmt: skip
                for k in range(1, 9)
            ],
        ]
    if filtros["sede"] != "0":
        return [
            {"idMostrar": 0, "nombreMostrar": "TOTAL SEDE", "encuestador": "TOTAL", **datos()},
            *[
                {
                    "idMostrar": k,
                    "usuario": f"{10000000 + k}",
                    "encuestador": f"ENCUESTADOR {k:02d}",
                    "activo": 1,
                    **datos(),
                }  # fmt: skip
                for k in range(1, 11)
            ],
        ]
    return [
        {"idMostrar": 0, "nombreMostrar": "NACIONAL", **datos()},
        *[{"idMostrar": k, "nombreMostrar": s, **datos()} for k, s in enumerate(_SEDES, 1)],
    ]


def _demo_mapa() -> list[dict]:
    import random

    r = random.Random("mapa")
    deps = ["AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA", "CALLAO",
            "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD", "LAMBAYEQUE",
            "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA", "PUNO",
            "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"]  # fmt: skip
    return [{"departamento": d, "indicador": round(r.uniform(1, 15), 1)} for d in deps]
