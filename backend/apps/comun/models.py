from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from .constantes import ODEI_NACIONAL, ODEIS, Cargo, Permiso


class UsuarioManager(BaseUserManager):
    def create_user(self, usuario, password=None, **extra):
        if not usuario:
            raise ValueError("El usuario es obligatorio")
        user = self.model(usuario=usuario, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, usuario, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("permisos", Permiso.SUPERVISAR)
        extra.setdefault("odei", ODEI_NACIONAL)
        return self.create_user(usuario, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuario del monitoreo. Conserva los campos del sistema actual (usuario, dni,
    odei, cargo, permisos) para poder migrar las cuentas existentes."""

    usuario = models.CharField(max_length=50, unique=True)
    dni = models.CharField(max_length=20, blank=True)
    nombres = models.CharField(max_length=100, blank=True)
    apellidos = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    odei = models.CharField(
        max_length=2,
        choices=ODEIS,
        default=ODEI_NACIONAL,
        help_text="Datos que puede ver: 00 = todo el país.",
    )
    cargo = models.CharField(max_length=2, choices=Cargo.OPCIONES, blank=True)
    permisos = models.CharField(
        max_length=1, choices=Permiso.OPCIONES, default=Permiso.DESHABILITADO
    )
    acceso_seguimiento = models.BooleanField(
        default=False,
        help_text="Acceso a 'Seguimiento del monitor' aunque su cargo no lo tenga.",
    )
    is_active = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("acceso al admin", default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "usuario"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        nombre = f"{self.nombres} {self.apellidos}".strip()
        return nombre or self.usuario

    @property
    def es_nacional(self) -> bool:
        return self.odei == ODEI_NACIONAL


class RegistroUso(models.Model):
    """Reemplaza a los procedimientos insertarIngreso / insertarSalida."""

    class Evento(models.TextChoices):
        INGRESO = "ingreso", "Ingreso"
        SALIDA = "salida", "Salida"

    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="registros_uso")
    pantalla = models.CharField(max_length=100)
    evento = models.CharField(max_length=10, choices=Evento.choices)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "registro de uso"
        verbose_name_plural = "registros de uso"
        indexes = [models.Index(fields=["pantalla", "fecha"])]
