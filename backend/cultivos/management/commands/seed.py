# Carga datos de ejemplo para probar el sistema

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from cultivos.models import (
    Ciclo, Cosecha, Cultivo, Empleado, EstadoLabor, Labor, Lote, Rol, TipoLabor, Usuario
)


class Command(BaseCommand):
    help = "Carga cultivos, lotes, empleados y un ciclo de ejemplo"

    def handle(self, *args, **opciones):
        if Usuario.objects.exists():
            self.stdout.write("La base de datos ya tiene informacion. No se carga nada.")
            return

        carlos = Empleado.objects.create(
            nombre="Carlos Ramirez", documento="1023456789",
            cargo="Fumigador", telefono="3001112233",
        )
        lucia = Empleado.objects.create(
            nombre="Lucia Mendoza", documento="1098765432",
            cargo="Recolectora", telefono="3014445566",
        )
        andres = Empleado.objects.create(
            nombre="Andres Patino", documento="1045678912",
            cargo="Agronomo", telefono="3027778899",
        )

        Usuario.objects.create_superuser(
            email="admin@cultivos.com", nombre="Sara Sofia", password="admin123",
        )
        Usuario.objects.create_user(
            email="carlos@cultivos.com", nombre="Carlos Ramirez", password="empleado123",
            rol=Rol.EMPLEADO, empleado=carlos,
        )

        mora = Cultivo.objects.create(
            nombre="Mora", variedad="Castilla", dias_ciclo=180, periodo_carencia_dias=15,
        )
        aguacate = Cultivo.objects.create(
            nombre="Aguacate", variedad="Hass", dias_ciclo=300, periodo_carencia_dias=21,
        )

        lote_a = Lote.objects.create(
            nombre="Lote A", ubicacion="Ladera norte",
            area_hectareas=Decimal("1.50"), cultivo=mora,
        )
        Lote.objects.create(
            nombre="Lote B", ubicacion="Vega del rio",
            area_hectareas=Decimal("2.75"), cultivo=aguacate,
        )

        hoy = date.today()
        inicio = hoy - timedelta(days=60)
        ciclo = Ciclo.objects.create(
            lote=lote_a,
            fecha_inicio=inicio,
            fecha_fin_estimada=inicio + timedelta(days=mora.dias_ciclo),
            observaciones="Primer ciclo de prueba",
        )

        Labor.objects.create(
            ciclo=ciclo, empleado=carlos, tipo=TipoLabor.FUMIGACION,
            estado=EstadoLabor.EJECUTADA, fecha_programada=hoy - timedelta(days=45),
            fecha_ejecucion=hoy - timedelta(days=45), producto="Mancozeb",
            dosis="2 g/L", costo=Decimal("120000"),
        )
        Labor.objects.create(
            ciclo=ciclo, empleado=andres, tipo=TipoLabor.FERTILIZACION,
            estado=EstadoLabor.EJECUTADA, fecha_programada=hoy - timedelta(days=30),
            fecha_ejecucion=hoy - timedelta(days=30), producto="Triple 15",
            dosis="50 g/planta", costo=Decimal("250000"),
        )
        Labor.objects.create(
            ciclo=ciclo, empleado=carlos, tipo=TipoLabor.FUMIGACION,
            estado=EstadoLabor.PROGRAMADA, fecha_programada=hoy + timedelta(days=7),
            producto="Azufre", dosis="3 g/L", costo=Decimal("95000"),
        )

        Cosecha.objects.create(
            ciclo=ciclo, empleado=lucia, fecha=hoy - timedelta(days=5),
            kilos=Decimal("340.50"), calidad="Primera",
        )

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados."))
        self.stdout.write("  Administrador: admin@cultivos.com / admin123")
        self.stdout.write("  Empleado:      carlos@cultivos.com / empleado123")
