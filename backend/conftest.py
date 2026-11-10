import pytest


@pytest.fixture(autouse=True)
def sin_sistema_actual(monkeypatch):
    """Las pruebas nunca consultan la base del sistema actual: por defecto no hay cuentas
    allí. Las pruebas de autenticación reemplazan esta función con cuentas de ejemplo."""
    monkeypatch.setattr("apps.comun.autenticacion.leer_usuario_actual", lambda usuario: None)
