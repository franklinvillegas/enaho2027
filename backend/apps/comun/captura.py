"""Acceso de SOLO LECTURA a la base de captura (ENAHO2014_BDCAPTURA).

Es la única puerta hacia la base de captura. Reglas:
  - Solo ejecuta procedimientos de una lista blanca (PROCEDIMIENTOS_PERMITIDOS).
  - Los parámetros siempre van enlazados, nunca pegados al texto del SQL.
  - Devuelve filas como diccionarios.
"""

from collections.abc import Sequence

from django.db import connections

from config.db_routers import CAPTURA

# Cada módulo registra aquí los procedimientos que usa mientras se migra.
PROCEDIMIENTOS_PERMITIDOS: set[str] = set()


class ProcedimientoNoPermitidoError(Exception):
    pass


def registrar_procedimientos(*nombres: str) -> None:
    PROCEDIMIENTOS_PERMITIDOS.update(nombres)


def ejecutar_procedimiento(nombre: str, parametros: Sequence = ()) -> list[dict]:
    if nombre not in PROCEDIMIENTOS_PERMITIDOS:
        raise ProcedimientoNoPermitidoError(nombre)
    marcadores = ", ".join(["%s"] * len(parametros))
    sql = f"EXEC dbo.[{nombre}] {marcadores}".strip()
    with connections[CAPTURA].cursor() as cursor:
        cursor.execute(sql, list(parametros))
        if cursor.description is None:
            return []
        columnas = [c[0] for c in cursor.description]
        return [dict(zip(columnas, fila, strict=True)) for fila in cursor.fetchall()]
