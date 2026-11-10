from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RegistroUso, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ["usuario"]
    list_display = ["usuario", "nombres", "apellidos", "odei", "cargo", "permisos", "is_active"]
    list_filter = ["odei", "cargo", "permisos", "is_active"]
    search_fields = ["usuario", "dni", "nombres", "apellidos"]
    fieldsets = [
        (None, {"fields": ["usuario", "password"]}),
        ("Datos personales", {"fields": ["dni", "nombres", "apellidos", "email"]}),
        ("Acceso", {"fields": ["odei", "cargo", "permisos", "acceso_seguimiento"]}),
        ("Administración", {"fields": ["is_active", "is_staff", "is_superuser", "groups"]}),
    ]
    add_fieldsets = [
        (None, {"fields": ["usuario", "password1", "password2", "odei", "cargo", "permisos"]}),
    ]
    filter_horizontal = ["groups"]


@admin.register(RegistroUso)
class RegistroUsoAdmin(admin.ModelAdmin):
    list_display = ["fecha", "usuario", "pantalla", "evento"]
    list_filter = ["evento", "pantalla"]
    date_hierarchy = "fecha"
