# Modelos del sistema de gestion de cultivos

from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Rol(models.TextChoices):
    ADMINISTRADOR = "administrador", "Administrador"
    EMPLEADO = "empleado", "Empleado"


class TipoLabor(models.TextChoices):
    FUMIGACION = "fumigacion", "Fumigacion"
    FERTILIZACION = "fertilizacion", "Fertilizacion"
    RIEGO = "riego", "Riego"
    PODA = "poda", "Poda"
    OTRA = "otra", "Otra"


class EstadoLabor(models.TextChoices):
    PROGRAMADA = "programada", "Programada"
    EJECUTADA = "ejecutada", "Ejecutada"
    CANCELADA = "cancelada", "Cancelada"


class EstadoCiclo(models.TextChoices):
    ACTIVO = "activo", "Activo"
    CERRADO = "cerrado", "Cerrado"


# Empleados

class Empleado(models.Model):
    nombre = models.CharField(max_length=120)
    documento = models.CharField(max_length=30, unique=True)
    cargo = models.CharField(max_length=60)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "empleados"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.cargo})"


# Usuarios del sistema

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra):
        if not email:
            raise ValueError("El correo es obligatorio")

        usuario = self.model(email=self.normalize_email(email), nombre=nombre, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, nombre, password=None, **extra):
        extra.setdefault("rol", Rol.ADMINISTRADOR)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, nombre, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=120)
    email = models.EmailField(max_length=120, unique=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.EMPLEADO)
    activo = models.BooleanField(default=True)
    empleado = models.OneToOneField(
        Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name="usuario"
    )
    is_staff = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    class Meta:
        db_table = "usuarios"
        ordering = ["nombre"]

    def __str__(self):
        return self.email

    @property
    def is_active(self):
        return self.activo

    @property
    def es_administrador(self):
        return self.rol == Rol.ADMINISTRADOR


# Cultivos y lotes

class Cultivo(models.Model):
    nombre = models.CharField(max_length=80)
    variedad = models.CharField(max_length=80, blank=True, null=True)
    dias_ciclo = models.PositiveIntegerField()
    periodo_carencia_dias = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "cultivos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Lote(models.Model):
    nombre = models.CharField(max_length=80)
    ubicacion = models.CharField(max_length=120, blank=True, null=True)
    area_hectareas = models.DecimalField(max_digits=8, decimal_places=2)
    cultivo = models.ForeignKey(Cultivo, on_delete=models.PROTECT, related_name="lotes")
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "lotes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# Ciclo productivo

class Ciclo(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="ciclos")
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField()
    fecha_fin_real = models.DateField(blank=True, null=True)
    estado = models.CharField(
        max_length=20, choices=EstadoCiclo.choices, default=EstadoCiclo.ACTIVO
    )
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "ciclos"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.lote.nombre} desde {self.fecha_inicio}"

    def save(self, *args, **kwargs):
        if not self.fecha_fin_estimada:
            self.fecha_fin_estimada = self.fecha_inicio + timedelta(
                days=self.lote.cultivo.dias_ciclo
            )
        super().save(*args, **kwargs)


# Labores de campo

class Labor(models.Model):
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE, related_name="labores")
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name="labores")
    tipo = models.CharField(max_length=20, choices=TipoLabor.choices)
    estado = models.CharField(
        max_length=20, choices=EstadoLabor.choices, default=EstadoLabor.PROGRAMADA
    )
    fecha_programada = models.DateField()
    fecha_ejecucion = models.DateField(blank=True, null=True)
    producto = models.CharField(max_length=120, blank=True, null=True)
    dosis = models.CharField(max_length=60, blank=True, null=True)
    costo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "labores"
        ordering = ["-fecha_programada"]

    def __str__(self):
        return f"{self.get_tipo_display()} del {self.fecha_programada}"


# Cosechas

class Cosecha(models.Model):
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE, related_name="cosechas")
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name="cosechas")
    fecha = models.DateField()
    kilos = models.DecimalField(max_digits=10, decimal_places=2)
    calidad = models.CharField(max_length=40, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cosechas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.kilos} kg el {self.fecha}"
