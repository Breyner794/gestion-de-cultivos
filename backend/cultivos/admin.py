# Panel de administracion de Django

from django.contrib import admin

from cultivos.models import Ciclo, Cosecha, Cultivo, Empleado, Labor, Lote, Usuario


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "documento", "cargo", "telefono", "activo"]
    list_filter = ["activo", "cargo"]
    search_fields = ["nombre", "documento"]


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ["nombre", "email", "rol", "activo"]
    list_filter = ["rol", "activo"]
    search_fields = ["nombre", "email"]


@admin.register(Cultivo)
class CultivoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "variedad", "dias_ciclo", "periodo_carencia_dias", "activo"]


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "cultivo", "ubicacion", "area_hectareas", "activo"]
    list_filter = ["cultivo", "activo"]


@admin.register(Ciclo)
class CicloAdmin(admin.ModelAdmin):
    list_display = ["lote", "fecha_inicio", "fecha_fin_estimada", "estado"]
    list_filter = ["estado"]


@admin.register(Labor)
class LaborAdmin(admin.ModelAdmin):
    list_display = ["tipo", "fecha_programada", "fecha_ejecucion", "empleado", "costo", "estado"]
    list_filter = ["tipo", "estado"]


@admin.register(Cosecha)
class CosechaAdmin(admin.ModelAdmin):
    list_display = ["fecha", "ciclo", "kilos", "calidad", "empleado"]
