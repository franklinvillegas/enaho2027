"""Filtros comunes a los indicadores.

En el sistema actual el mismo concepto tenía varios nombres (depart / departamento /
odei; funcionario / encues / encuestador) y el rango llegaba en cuatro piezas en la
URL. Aquí hay un solo nombre por concepto y llegan como parámetros de consulta:

    ?nivel=odei&odei=15&periodo_inicio=0&mes_inicio=1&periodo_fin=0&mes_fin=6

Valores tomados de las pantallas actuales (tnr_total.html):
  - mes: 1 a 12, o 0 = sin filtro. Se envía al procedimiento con dos dígitos ("01", "00").
  - periodo: 1 a 5, o 0 = todos.
  - excluir: 0 sin exclusiones, 1 no panel, 2 panel, 3 panel ausente sin teléfono.
"""

from rest_framework import serializers

from .constantes import ODEI_NACIONAL, ODEIS


class Nivel:
    DEPARTAMENTO = "departamento"
    ODEI = "odei"
    CONGLOMERADO = "conglomerado"
    OPCIONES = [DEPARTAMENTO, ODEI, CONGLOMERADO]


class FiltrosIndicadorSerializer(serializers.Serializer):
    nivel = serializers.ChoiceField(choices=Nivel.OPCIONES, default=Nivel.DEPARTAMENTO)
    periodo_inicio = serializers.IntegerField(min_value=0, max_value=5, default=0)
    periodo_fin = serializers.IntegerField(min_value=0, max_value=5, default=0)
    mes_inicio = serializers.IntegerField(min_value=0, max_value=12, default=0)
    mes_fin = serializers.IntegerField(min_value=0, max_value=12, default=0)
    odei = serializers.ChoiceField(choices=[c for c, _ in ODEIS], required=False)
    encuestador = serializers.RegexField(r"^[0-9A-Za-z_]{1,20}$", required=False)
    conglomerado = serializers.RegexField(r"^[0-9]{6}$", required=False)
    solo_activos = serializers.BooleanField(default=False)
    excluir = serializers.ChoiceField(choices=[0, 1, 2, 3], default=0)

    def validate(self, datos):
        # Mismas reglas que las pantallas actuales
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
        if datos["nivel"] in (Nivel.ODEI, Nivel.CONGLOMERADO) and not datos.get("odei"):
            raise serializers.ValidationError({"odei": "Requerido para este nivel."})
        return datos

    def aplicar_alcance(self, datos: dict, usuario) -> dict:
        """Un usuario de una ODEI solo ve su ODEI, aunque pida otra."""
        if usuario.odei and usuario.odei != ODEI_NACIONAL:
            datos["odei"] = usuario.odei
        return datos
