from django.apps import AppConfig


class CoberturaConfig(AppConfig):
    name = "apps.cobertura"
    verbose_name = "Indicadores de cobertura"

    def ready(self):
        from . import repositorios  # noqa: F401  (registra los procedimientos permitidos)
