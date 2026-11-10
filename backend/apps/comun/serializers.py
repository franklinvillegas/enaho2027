from rest_framework import serializers

from .acceso import modulos_permitidos
from .models import RegistroUso, Usuario


class LoginSerializer(serializers.Serializer):
    usuario = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class UsuarioActualSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source="__str__")
    modulos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["usuario", "nombre", "odei", "cargo", "permisos", "modulos"]

    def get_modulos(self, obj) -> list[str]:
        return modulos_permitidos(obj)


class RegistroUsoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroUso
        fields = ["pantalla", "evento"]
