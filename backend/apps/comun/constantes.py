"""Catálogos fijos tomados del sistema actual (usuarios/models.py de monitoreo-enaho-v2)."""

ODEIS = [
    ("00", "NACIONAL"),
    ("01", "AMAZONAS"),
    ("02", "ANCASH-HUARAZ"),
    ("03", "ANCASH-CHIMBOTE"),
    ("04", "APURIMAC"),
    ("05", "AREQUIPA"),
    ("06", "AYACUCHO"),
    ("07", "CAJAMARCA"),
    ("08", "CUSCO"),
    ("09", "HUANCAVELICA"),
    ("10", "HUANUCO"),
    ("11", "ICA"),
    ("12", "JUNIN"),
    ("13", "LA LIBERTAD"),
    ("14", "LAMBAYEQUE"),
    ("15", "LIMA"),
    ("16", "LORETO"),
    ("17", "MADRE DE DIOS"),
    ("18", "MOQUEGUA"),
    ("19", "PASCO"),
    ("20", "PIURA"),
    ("21", "PUNO"),
    ("22", "SAN MARTIN-MOYOBAMBA"),
    ("23", "SAN MARTIN-TARAPOTO"),
    ("24", "TACNA"),
    ("25", "TUMBES"),
    ("26", "UCAYALI"),
]

ODEI_NACIONAL = "00"


class Cargo:
    ANALISTA_PROGRAMADOR = "01"
    ANALISTA_CONSISTENCIA = "02"
    COORDINADOR_DEPARTAMENTAL = "03"
    DIRECTOR = "04"
    ENCUESTADOR = "05"
    JEFE_OPERACION_CAMPO = "06"
    JEFE_PROYECTO = "07"
    METODOLOGO = "08"
    MONITOR = "09"
    OPERADOR_PROCESOS = "10"
    SUPERVISOR_LOCAL = "11"
    SUPERVISOR_NACIONAL = "12"
    UDRA = "13"

    OPCIONES = [
        ("01", "ANALISTA PROGRAMADOR(A) / INFORMÁTICO"),
        ("02", "ANALISTA CONSISTENCIA FINAL"),
        ("03", "COORDINADOR(A) DEPARTAMENTAL"),
        ("04", "DIRECTOR(A)"),
        ("05", "ENCUESTADOR(A)"),
        ("06", "JEFE OPERACIÓN DE CAMPO"),
        ("07", "JEFE PROYECTO"),
        ("08", "METODÓLOGO"),
        ("09", "MONITOR(A)"),
        ("10", "OPERADOR(A) PROCESOS INFORMÁTICOS"),
        ("11", "SUPERVISOR(A) LOCAL"),
        ("12", "SUPERVISOR(A) NACIONAL"),
        ("13", "UDRA"),
    ]


class Permiso:
    DESHABILITADO = "0"
    SUPERVISAR = "1"
    ENCUESTAR = "2"

    OPCIONES = [
        ("0", "Deshabilitado"),
        ("1", "Supervisar"),
        ("2", "Encuestar"),
    ]


class Modulo:
    """Módulos del menú. El código se usa en la API, en permisos y en el frontend."""

    OPERACION_CAMPO = "operacion_campo"
    REPORTES_CAMPO = "reportes_campo"
    COBERTURA = "cobertura"
    CALIDAD = "calidad"
    VALORES_MONETARIOS = "valores_monetarios"
    SEGUIMIENTO_MONITOR = "seguimiento_monitor"

    TODOS = [
        OPERACION_CAMPO,
        REPORTES_CAMPO,
        COBERTURA,
        CALIDAD,
        VALORES_MONETARIOS,
        SEGUIMIENTO_MONITOR,
    ]
