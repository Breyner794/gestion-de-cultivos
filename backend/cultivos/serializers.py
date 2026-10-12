# Validacion de entrada y salida de la API

from datetime import timedelta

from rest_framework import serializers

from cultivos.models import (
    Ciclo, Cosecha, Cultivo, Empleado, EstadoCiclo, EstadoLabor, Labor, Lote, Usuario
)


# Usuarios

class UsuarioSerializer(serializers.ModelSerializer):
    empleado_id = serializers.IntegerField(source="empleado.id", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "rol", "activo", "empleado_id"]


class UsuarioCrearSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "password", "rol", "empleado"]

    def create(self, datos):
        password = datos.pop("password")
        return Usuario.objects.create_user(password=password, **datos)


# Empleados

class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ["id", "nombre", "documento", "cargo", "telefono", "activo"]


# Cultivos y lotes

class CultivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cultivo
        fields = ["id", "nombre", "variedad", "dias_ciclo", "periodo_carencia_dias", "activo"]


class LoteSerializer(serializers.ModelSerializer):
    cultivo_id = serializers.PrimaryKeyRelatedField(
        source="cultivo", queryset=Cultivo.objects.all()
    )
    cultivo = CultivoSerializer(read_only=True)

    class Meta:
        model = Lote
        fields = ["id", "nombre", "ubicacion", "area_hectareas", "cultivo_id", "cultivo", "activo"]


# Ciclo productivo

class CicloSerializer(serializers.ModelSerializer):
    lote_id = serializers.PrimaryKeyRelatedField(source="lote", queryset=Lote.objects.all())
    lote = LoteSerializer(read_only=True)

    class Meta:
        model = Ciclo
        fields = [
            "id", "lote_id", "lote", "fecha_inicio", "fecha_fin_estimada",
            "fecha_fin_real", "estado", "observaciones",
        ]
        read_only_fields = ["fecha_fin_estimada", "fecha_fin_real", "estado"]

    def validate(self, datos):
        lote = datos["lote"]
        if Ciclo.objects.filter(lote=lote, estado=EstadoCiclo.ACTIVO).exists():
            raise serializers.ValidationError("Este lote ya tiene un ciclo activo")
        return datos

    def create(self, datos):
        datos["fecha_fin_estimada"] = datos["fecha_inicio"] + timedelta(
            days=datos["lote"].cultivo.dias_ciclo
        )
        return super().create(datos)


# Labores de campo

class LaborSerializer(serializers.ModelSerializer):
    ciclo_id = serializers.PrimaryKeyRelatedField(source="ciclo", queryset=Ciclo.objects.all())
    empleado_id = serializers.PrimaryKeyRelatedField(
        source="empleado", queryset=Empleado.objects.all()
    )
    empleado = EmpleadoSerializer(read_only=True)

    class Meta:
        model = Labor
        fields = [
            "id", "ciclo_id", "empleado_id", "empleado", "tipo", "estado",
            "fecha_programada", "fecha_ejecucion", "producto", "dosis",
            "costo", "observaciones",
        ]
        read_only_fields = ["estado"]

    def validate(self, datos):
        """Caso de uso de apoyo: seleccionar empleado responsable y validar datos."""
        ciclo = datos.get("ciclo")
        if ciclo and ciclo.estado == EstadoCiclo.CERRADO:
            raise serializers.ValidationError(
                "No se pueden registrar labores en un ciclo cerrado"
            )

        empleado = datos.get("empleado")
        if empleado and not empleado.activo:
            raise serializers.ValidationError("El empleado esta inactivo")

        return datos

    def create(self, datos):
        datos["estado"] = (
            EstadoLabor.EJECUTADA if datos.get("fecha_ejecucion") else EstadoLabor.PROGRAMADA
        )
        return super().create(datos)

    def update(self, instancia, datos):
        datos["estado"] = (
            EstadoLabor.EJECUTADA if datos.get("fecha_ejecucion") else EstadoLabor.PROGRAMADA
        )
        return super().update(instancia, datos)


class LaborEjecutarSerializer(serializers.Serializer):
    fecha_ejecucion = serializers.DateField()
    costo = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)


# Cosechas

class CosechaSerializer(serializers.ModelSerializer):
    ciclo_id = serializers.PrimaryKeyRelatedField(source="ciclo", queryset=Ciclo.objects.all())
    empleado_id = serializers.PrimaryKeyRelatedField(
        source="empleado", queryset=Empleado.objects.all()
    )
    empleado = EmpleadoSerializer(read_only=True)

    class Meta:
        model = Cosecha
        fields = [
            "id", "ciclo_id", "empleado_id", "empleado", "fecha",
            "kilos", "calidad", "observaciones",
        ]

    def validate(self, datos):
        ciclo = datos["ciclo"]

        if ciclo.estado == EstadoCiclo.CERRADO:
            raise serializers.ValidationError("El ciclo ya esta cerrado")
        if datos["fecha"] < ciclo.fecha_inicio:
            raise serializers.ValidationError(
                "La cosecha no puede ser anterior al inicio del ciclo"
            )
        if not datos["empleado"].activo:
            raise serializers.ValidationError("El empleado esta inactivo")

        self.verificar_periodo_carencia(ciclo, datos["fecha"])
        return datos

    def verificar_periodo_carencia(self, ciclo, fecha_cosecha):
        """Caso de uso de apoyo: sin esta verificacion la cosecha no se registra."""
        carencia = ciclo.lote.cultivo.periodo_carencia_dias
        if carencia <= 0:
            return

        ultima = (
            Labor.objects.filter(
                ciclo=ciclo,
                tipo="fumigacion",
                estado=EstadoLabor.EJECUTADA,
                fecha_ejecucion__isnull=False,
            )
            .order_by("-fecha_ejecucion")
            .values_list("fecha_ejecucion", flat=True)
            .first()
        )
        if not ultima:
            return

        habilitada = ultima + timedelta(days=carencia)
        if fecha_cosecha < habilitada:
            raise serializers.ValidationError(
                f"El lote esta en periodo de carencia. Ultima fumigacion: {ultima}. "
                f"Se puede cosechar desde el {habilitada}."
            )
