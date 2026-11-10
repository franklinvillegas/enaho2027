"""La base del sistema actual (ENAHO2019_BDMONITOREO) es de SOLO LECTURA para este sistema.

Ningún modelo de Django vive en ella, y no se permite escribir ni migrar ahí.
Se lee explícitamente con connections["sistema_actual"] desde apps/comun/sistema_actual.py
y apps/comun/autenticacion.py.
"""

SISTEMA_ACTUAL = "sistema_actual"


class SistemaActualSoloLecturaRouter:
    def db_for_read(self, model, **hints):
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db != SISTEMA_ACTUAL
