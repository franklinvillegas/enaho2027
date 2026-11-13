"""Consulta de los indicadores de calidad (y sus datos de demostración)."""

import random
from datetime import date

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.comun import sistema_actual
from apps.comun.constantes import ODEI_NACIONAL, ODEIS

from .indicadores import NINI, obtener, todos


class FiltrosCalidadSerializer(serializers.Serializer):
    indicador = serializers.IntegerField(min_value=1, max_value=999)
    sede = serializers.RegexField(r"^\d{1,2}(\.\d)?$", default="0")
    usuario = serializers.RegexField(r"^[0-9A-Za-z_]{1,20}$", default="0")
    conglomerado = serializers.RegexField(r"^(0|\d{6})$", default="0")
    mes_inicio = serializers.IntegerField(min_value=0, max_value=12, default=0)
    mes_fin = serializers.IntegerField(min_value=0, max_value=12, default=0)
    periodo_inicio = serializers.IntegerField(min_value=0, max_value=5, default=0)
    periodo_fin = serializers.IntegerField(min_value=0, max_value=5, default=0)
    # 4 y 5 (con / sin supervisión) solo en consumo de alimentos
    excluir = serializers.ChoiceField(choices=[0, 1, 2, 3, 4, 5], default=0)
    # "Visualizar casos" y precios: ODEI del combo (0 = todas)
    odei = serializers.RegexField(r"^\d{1,2}$", default="0")
    # Pirámide de edad: departamento ("00" = nacional)
    departamento = serializers.RegexField(r"^\d{2}$", default="00")
    # Precios: año, mes y producto
    anio = serializers.IntegerField(min_value=2013, max_value=2100, default=date.today().year)
    mes = serializers.IntegerField(min_value=0, max_value=12, default=0)
    producto = serializers.RegexField(r"^\d{6}$", default="000000")
    # Tasa de asistencia escolar: 0 sin dominio, 1 sexo, 2 grupo de edad, 3 centro de estudios
    dominio = serializers.IntegerField(min_value=0, max_value=3, default=0)

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


def consultar(pantalla: str, vista: str, f: dict) -> list[dict]:
    llamadas = obtener(pantalla, vista, f["indicador"])
    if settings.FUENTE_COBERTURA == "demo":
        return demo(pantalla, vista, f)
    filas = []
    # Una llamada a la vez (como la pantalla actual, pero sin saturar el servidor)
    for ll in llamadas(f):
        datos = sistema_actual.ejecutar_procedimiento(
            ll.procedimiento, [str(p) for p in ll.parametros]
        )
        filas.extend({**fila, **ll.extra} for fila in datos)
    return filas


# ---------------------------------------------------------------------------------------
# Demostración (FUENTE_COBERTURA=demo): mismas columnas que devuelven los procedimientos
# ---------------------------------------------------------------------------------------

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "setiembre", "octubre", "noviembre", "diciembre"]  # fmt: skip
_DEPARTAMENTOS = ["AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
                  "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD",
                  "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA",
                  "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"]  # fmt: skip
_ETNIAS = [
    "Quechua",
    "Aymara",
    "Nativo o Indígena de la Amazonía",
    "Negro/Moreno/Mulato/Zambo/Afroperuano",
    "Blanco",
    "Mestizo",
    "Otro",
    "No Sabe",
]
_TRIMESTRES = [
    "janfebmar",
    "febmarapr",
    "maraprmay",
    "aprmayjun",
    "mayjunjul",
    "junjulaug",
    "julaugsep",
    "augsepoct",
    "sepoctnov",
    "octnovdec",
    "novdecjan",
    "decjanfeb",
]
_MES_PET = ["ene", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _casos_demo(r, extra):
    anio = date.today().year
    return [
        {"id": k, "año": anio, "a": anio, "odei": "14", "nomodei": "LAMBAYEQUE",
         "mes": f"{r.randint(1, 12):02d}", "periodo": r.randint(1, 5),
         "conglome": f"{r.randint(1, 999999):06d}", "vivienda": f"{r.randint(1, 140):03d}",
         "hogar": "11", "result": 1, "codencue": f"{40000000 + k}",
         "nomencue": f"ENCUESTADOR {k:02d}", **extra(r)}
        for k in range(1, 21)
    ]  # fmt: skip


def _balance(r):
    return {
        "ingreso_total": round(r.uniform(800, 5000), 2),
        **{f"ingreso0{n}": round(r.uniform(0, 900), 2) for n in range(1, 6)},
        "ingreso_trabajo": round(r.uniform(0, 3000), 2),
        "alquiler_imputado": round(r.uniform(0, 600), 2),
        "gasto_total": round(r.uniform(800, 6000), 2),
        **{f"gasto0{n}": round(r.uniform(0, 900), 2) for n in range(1, 9)},
        "gasto_alimentosbebidas": round(r.uniform(200, 1500), 2),
        "gasto_alimentosdentrohogar": round(r.uniform(100, 900), 2),
        "balance": round(r.uniform(-80, -20), 1),
    }


def _niveles(f, r, datos, vista):
    """Filas tipo: total + ODEI / encuestadores / conglomerados / viviendas según el nivel."""
    sede, usuario = todos(f["sede"], "0"), todos(f["usuario"], "0")
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
            {"id": k, "idMostrar": sede, "nombreMostrar": nombre_sede,
             "usuario": f"{10000000 + k}", "encuestador": f"ENCUESTADOR {k:02d}", **datos()}
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


def demo(pantalla: str, vista: str, f: dict) -> list[dict]:  # noqa: C901 (datos inventados)
    ind = f["indicador"]
    r = random.Random(f"cal-{pantalla}-{vista}-{ind}-{f['sede']}-{f['usuario']}-{f['dominio']}")
    anio = date.today().year
    base = 2.5 if ind in (1, 2, 44) else r.uniform(5, 90)

    def v(b=None):
        b = base if b is None else b
        return round(max(0.0, b + r.uniform(-b * 0.2, b * 0.2)), 2)

    if vista == "casos":
        extra = {
            65: _balance, 66: _balance,
            67: lambda r: {"miembros_hogar": r.randint(1, 9)},
            68: lambda r: {"gastos_canasta": round(r.uniform(100, 1500), 2)},
        }[ind]  # fmt: skip
        return _casos_demo(r, extra)
    if vista == "encuestadores":
        return [{"value": f"{40000000 + k}", "texto": f"ENCUESTADOR {k:02d}"} for k in range(1, 9)]
    if vista == "piramide":
        rangos = [f"{a} - {a + 4}" for a in range(0, 95, 5)] + ["95 a más"]
        filas = []
        for a in (anio, anio - 1, anio - 2):
            pv, pm = [r.uniform(1, 6) for _ in rangos], [r.uniform(1, 6) for _ in rangos]
            filas.append({"nom_rango": "TOTAL", "varones": 25000, "mujeres": 26000,
                          "porcVarones": 100, "porcMujeres": 100, "porcVaronesProyec": 100,
                          "porcMujeresProyec": 100, "anio_piramide": a})  # fmt: skip
            filas += [
                {"nom_rango": n, "varones": int(x * 250), "mujeres": int(y * 260),
                 "porcVarones": round(x * 2, 1), "porcMujeres": round(y * 2, 1),
                 "porcVaronesProyec": round(x * 2 + r.uniform(-0.4, 0.4), 1),
                 "porcMujeresProyec": round(y * 2 + r.uniform(-0.4, 0.4), 1), "anio_piramide": a}
                for n, x, y in zip(rangos, sorted(pv, reverse=True), sorted(pm, reverse=True),
                                   strict=True)
            ]  # fmt: skip
        return filas
    if vista == "precios":
        productos = ["ARROZ CORRIENTE", "AZUCAR RUBIA", "ACEITE VEGETAL", "LECHE EVAPORADA",
                     "PAPA BLANCA", "POLLO EVISCERADO", "HUEVO DE GALLINA", "PAN FRANCES",
                     "FIDEOS", "CEBOLLA ROJA", "TOMATE", "LIMON", "PLATANO", "CARNE DE RES",
                     "ATUN EN CONSERVA", "QUESO FRESCO", "ZANAHORIA", "AJO", "LENTEJA",
                     "MANZANA", "NARANJA", "YUCA"]  # fmt: skip
        nombre = dict(ODEIS).get(f"{int(f['odei'] or 1):02d}", "ODEI")
        filas = []
        for k, p in enumerate(productos, 1):
            actual, anterior = round(r.uniform(1, 25), 2), round(r.uniform(1, 25), 2)
            filas.append({"id": k, "año": f["anio"], "mes": f"{f['mes'] or 1:02d}",
                          "nom_odei": nombre, "cod_prod": f"{100000 + k * 37:06d}", "descrip": p,
                          "precio_enaho": actual, "precio_anio_anterior": anterior,
                          "diferencia": round(actual - anterior, 2)})  # fmt: skip
        return filas
    if vista == "precios-provincias":
        return [{"id": k, "anio": f["anio"], "mes": f"{f['mes'] or 1:02d}", "nomodei": "ODEI",
                 "provincia": f"PROVINCIA {k}", "produc": f["producto"], "descripcion": "PRODUCTO",
                 "precio_enaho": round(r.uniform(1, 25), 2)} for k in range(1, 8)]  # fmt: skip
    if vista == "precios-lista":
        return [{"id": k, "año": f["anio"], "mes": f"{f['mes'] or 1:02d}", "nomodei": "ODEI",
                 "estrato": r.randint(1, 8), "conglome": f"{r.randint(1, 999999):06d}",
                 "vivienda": f"{r.randint(1, 140):03d}", "hogar": "11", "produc61": f["producto"],
                 "descrip": "PRODUCTO", "frec_des": "DIARIO", "lugar_compra": "MERCADO",
                 "p601a": 1, "cantidad": r.randint(1, 5), "unid_med_des": "KILOGRAMO",
                 "monto_compra": round(r.uniform(2, 60), 2), "precio": round(r.uniform(1, 25), 2)}
                for k in range(1, 15)]  # fmt: skip
    if vista == "trimestral":
        nombres = ["PET", "PEA", "Ocupados", "Desocupados", "NO PEA", "Tasa de actividad",
                   "Tasa de desempleo"]  # fmt: skip
        return [{"idMostrar": k, "orden": k, "nombreMostrar": n,
                 **{f"{t}{s}": round(r.uniform(100, 900), 1) for t in _TRIMESTRES
                    for s in (2016, 2017)}} for k, n in enumerate(nombres, 1)]  # fmt: skip
    if vista == "pet":
        filas = [{"serie": "anual", "anio": str(a), "pet": v(75), "pea": v(70), "ocupados": v(66)}
                 for a in range(2016, anio + 1)]  # fmt: skip
        filas += [{"serie": "mensual", "anio": str(a),
                   **{f"{m}_{t}": v(b) for m in _MES_PET for t, b in
                      (("pet", 75), ("pea", 70), ("ocupados", 66))}}
                  for a in (anio - 1, anio)]  # fmt: skip
        return filas
    if ind == 36:  # etnicidad: filas largas (nombre, año, valor), % y número de casos
        filas = []
        for orden, ubicacion in enumerate(["Perú", "Urbano", "Rural"], 1):
            for id2, nombre in enumerate([ubicacion, *_ETNIAS]):
                pct = [round(r.uniform(1, 40), 1) for _ in range(2012, anio + 1)]
                for bloque in (pct, [int(p * 50) for p in pct]):
                    filas += [
                        {
                            "orden": str(orden),
                            "id2": str(id2),
                            "nombre": nombre,
                            "anio": str(a),
                            "indicador": x,
                        }
                        for a, x in zip(range(2012, anio + 1), bloque, strict=True)
                    ]
        return filas

    def datos():
        if vista == "odei-mes":
            if ind == 91 and f["dominio"]:
                n = 3 if f["dominio"] == 2 else 2
                fila = {}
                for k in range(1, n + 1):
                    for suf in (f"Anterior{k}b", f"Anterior{k}", f"Actual{k}"):
                        fila[f"indicador{suf}"] = v()
                        fila.update({f"{m}{suf}": v() for m in _MESES})
                return fila
            fila = {}
            for suf in ("Anterior2", "Anterior", "Actual"):
                fila[f"indicador{suf}"] = v()
                fila.update({f"{m}{suf}": v() for m in _MESES})
            return fila
        if ind == 31:
            return {f"indicador{a}{x}": v(25) for a in range(2018, anio + 1) for x in "abcd"}
        if ind == 91 and f["dominio"] and vista == "odei":
            sufijos = {1: ("_h", "_m"), 2: ("_ini", "_pri", "_sec"), 3: ("_e", "_ne")}[f["dominio"]]
            return {f"indicador{a}{s}": v() for a in range(2013, anio + 1) for s in sufijos}
        fila = {f"indicador{a}": v() for a in range(2013, anio + 1)}
        fila["Estado"] = r.choice(["Aceptable", "Revisar"])
        return fila

    if ind == 31 and vista == "odei-mes":
        return [{**fila, "grupo": g} for g in NINI for fila in _niveles(f, r, datos, vista)]
    return _niveles(f, r, datos, vista)
