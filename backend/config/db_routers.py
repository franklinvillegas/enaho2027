"""La base de captura es de SOLO LECTURA para este sistema.

Ningún modelo de Django vive en ella, y no se permite escribir ni migrar ahí.
Las lecturas a captura se hacen explícitamente con connections["captura"]
desde los repositorios de cada módulo.
"""

CAPTURA = "captura"


class CapturaSoloLecturaRouter:
    def db_for_read(self, model, **hints):
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db != CAPTURA
