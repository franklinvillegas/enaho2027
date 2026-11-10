"""Filtros comunes a los indicadores.

En el sistema actual el mismo concepto tenía varios nombres (depart / departamento /
odei; funcionario / encues / encuestador) y el rango llegaba en cuatro piezas en la
URL. Aquí hay un solo nombre por concepto y llegan como parámetros de consulta:

    ?nivel=odei&odei=15&periodo_inicio=1&mes_inicio=1&periodo_fin=3&mes_fin=6
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
    periodo_inicio = serializers.IntegerField(min_value=1, max_value=9)
    periodo_fin = serializers.IntegerField(min_value=1, max_value=9)
    mes_inicio = serializers.IntegerField(min_value=1, max_value=12)
    mes_fin = serializers.IntegerField(min_value=1, max_value=12)
    odei = serializers.ChoiceField(choices=[c for c, _ in ODEIS], required=False)
    encuestador = serializers.RegexField(r"^[0-9A-Za-z_]{1,20}$", required=False)
    conglomerado = serializers.RegexField(r"^[0-9]{6}$", required=False)
    solo_activos = serializers.BooleanField(default=False)
    excluir = serializers.RegexField(r"^[0-9A-Za-z,]{0,50}$", required=False, allow_blank=True)

    def validate(self, datos):
        # Pendiente: validar que el inicio del rango no sea posterior al fin, cuando se
        # confirme con los procedimientos cómo se combinan periodo y mes.
        if datos["nivel"] in (Nivel.ODEI, Nivel.CONGLOMERADO) and not datos.get("odei"):
            raise serializers.ValidationError({"odei": "Requerido para este nivel."})
        return datos

    def aplicar_alcance(self, datos: dict, usuario) -> dict:
        """Un usuario de una ODEI solo ve su ODEI, aunque pida otra."""
        if usuario.odei and usuario.odei != ODEI_NACIONAL:
            datos["odei"] = usuario.odei
        return datos
