# Vistas de la API

import csv
import io
from datetime import date

from django.db.models import Count, DecimalField, Sum
from django.http import HttpResponse
from django.db.models.functions import Coalesce
from openpyxl import Workbook
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from cultivos.models import (
    Ciclo, Cosecha, Cultivo, Empleado, EstadoCiclo, EstadoLabor, Labor, Lote, Rol, Usuario
)
from cultivos.permissions import AdministradorEscribeEmpleadoLee, SoloAdministrador
from cultivos.serializers import (
    CicloSerializer, CosechaSerializer, CultivoSerializer, EmpleadoSerializer,
    LaborEjecutarSerializer, LaborSerializer, LoteSerializer, UsuarioCrearSerializer,
    UsuarioSerializer,
)

CERO = Coalesce(Sum("costo"), 0, output_field=DecimalField())
ENCABEZADOS = ["Fecha", "Lote", "Cultivo", "Tipo", "Estado", "Empleado", "Producto", "Costo"]


# Autenticacion

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate

        email = request.data.get("username") or request.data.get("email")
        password = request.data.get("password")
        usuario = authenticate(request, email=email, password=password)

        if not usuario:
            return Response(
                {"detail": "Correo o contrasena incorrectos"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = RefreshToken.for_user(usuario)
        return Response({"access_token": str(token.access_token), "token_type": "bearer"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mi_perfil(request):
    return Response(UsuarioSerializer(request.user).data)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = [SoloAdministrador]

    def get_serializer_class(self):
        return UsuarioCrearSerializer if self.action == "create" else UsuarioSerializer


# Empleados

class EmpleadoViewSet(viewsets.ModelViewSet):
    serializer_class = EmpleadoSerializer
    permission_classes = [AdministradorEscribeEmpleadoLee]

    def get_queryset(self):
        consulta = Empleado.objects.all()
        if self.request.query_params.get("solo_activos") == "true":
            consulta = consulta.filter(activo=True)
        return consulta

    def perform_destroy(self, instancia):
        instancia.activo = False
        instancia.save()


# Cultivos y lotes

class CultivoViewSet(viewsets.ModelViewSet):
    queryset = Cultivo.objects.all()
    serializer_class = CultivoSerializer
    permission_classes = [AdministradorEscribeEmpleadoLee]

    def perform_destroy(self, instancia):
        instancia.activo = False
        instancia.save()


class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.select_related("cultivo").all()
    serializer_class = LoteSerializer
    permission_classes = [AdministradorEscribeEmpleadoLee]

    def perform_destroy(self, instancia):
        if instancia.ciclos.filter(estado=EstadoCiclo.ACTIVO).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError("No se puede desactivar un lote con un ciclo activo")

        instancia.activo = False
        instancia.save()


# Ciclo productivo

class CicloViewSet(viewsets.ModelViewSet):
    serializer_class = CicloSerializer
    permission_classes = [AdministradorEscribeEmpleadoLee]

    def get_queryset(self):
        consulta = Ciclo.objects.select_related("lote__cultivo").all()
        estado = self.request.query_params.get("estado")
        return consulta.filter(estado=estado) if estado else consulta

    @action(detail=False, methods=["get"])
    def estado(self, request):
        hoy = date.today()
        resultado = []

        for ciclo in self.get_queryset().filter(estado=EstadoCiclo.ACTIVO):
            total = (ciclo.fecha_fin_estimada - ciclo.fecha_inicio).days or 1
            transcurridos = max((hoy - ciclo.fecha_inicio).days, 0)

            resultado.append({
                "id": ciclo.id,
                "lote": ciclo.lote.nombre,
                "cultivo": ciclo.lote.cultivo.nombre,
                "estado": ciclo.estado,
                "fecha_inicio": ciclo.fecha_inicio,
                "fecha_fin_estimada": ciclo.fecha_fin_estimada,
                "dias_transcurridos": transcurridos,
                "dias_restantes": (ciclo.fecha_fin_estimada - hoy).days,
                "porcentaje_avance": round(min(transcurridos / total * 100, 100), 1),
            })

        return Response(resultado)

    @action(detail=True, methods=["post"], permission_classes=[SoloAdministrador])
    def cerrar(self, request, pk=None):
        ciclo = self.get_object()

        if ciclo.estado == EstadoCiclo.CERRADO:
            return Response(
                {"detail": "El ciclo ya esta cerrado"}, status=status.HTTP_409_CONFLICT
            )

        ciclo.estado = EstadoCiclo.CERRADO
        ciclo.fecha_fin_real = date.today()
        ciclo.save()
        return Response(CicloSerializer(ciclo).data)


# Labores de campo

class LaborViewSet(viewsets.ModelViewSet):
    serializer_class = LaborSerializer
    permission_classes = [AdministradorEscribeEmpleadoLee]

    def get_queryset(self):
        consulta = Labor.objects.select_related("empleado", "ciclo__lote__cultivo").all()

        if self.request.user.rol == Rol.EMPLEADO:
            consulta = consulta.filter(empleado=self.request.user.empleado)

        for campo in ("ciclo_id", "tipo", "estado"):
            valor = self.request.query_params.get(campo)
            if valor:
                consulta = consulta.filter(**{campo: valor})

        return consulta

    @action(detail=False, methods=["get"])
    def proximas(self, request):
        consulta = self.get_queryset().filter(
            estado=EstadoLabor.PROGRAMADA, fecha_programada__gte=date.today()
        ).order_by("fecha_programada")
        return Response(LaborSerializer(consulta, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[SoloAdministrador])
    def ejecutar(self, request, pk=None):
        labor = self.get_object()

        if labor.estado == EstadoLabor.EJECUTADA:
            return Response(
                {"detail": "La labor ya fue ejecutada"}, status=status.HTTP_409_CONFLICT
            )

        datos = LaborEjecutarSerializer(data=request.data)
        datos.is_valid(raise_exception=True)

        labor.fecha_ejecucion = datos.validated_data["fecha_ejecucion"]
        labor.estado = EstadoLabor.EJECUTADA
        if datos.validated_data.get("costo") is not None:
            labor.costo = datos.validated_data["costo"]
        if datos.validated_data.get("observaciones"):
            labor.observaciones = datos.validated_data["observaciones"]
        labor.save()

        return Response(LaborSerializer(labor).data)

    def perform_destroy(self, instancia):
        instancia.estado = EstadoLabor.CANCELADA
        instancia.save()


# Cosechas

class CosechaViewSet(viewsets.ModelViewSet):
    serializer_class = CosechaSerializer
    permission_classes = [AdministradorEscribeEmpleadoLee]

    def get_queryset(self):
        consulta = Cosecha.objects.select_related("empleado", "ciclo__lote").all()

        if self.request.user.rol == Rol.EMPLEADO:
            consulta = consulta.filter(empleado=self.request.user.empleado)

        ciclo_id = self.request.query_params.get("ciclo_id")
        return consulta.filter(ciclo_id=ciclo_id) if ciclo_id else consulta

    @action(detail=False, methods=["get"], url_path="kilaje/(?P<ciclo_id>[^/.]+)")
    def kilaje(self, request, ciclo_id=None):
        try:
            ciclo = Ciclo.objects.select_related("lote").get(pk=ciclo_id)
        except Ciclo.DoesNotExist:
            return Response(
                {"detail": "Ciclo no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        cosechas = Cosecha.objects.filter(ciclo=ciclo)
        total = cosechas.aggregate(
            t=Coalesce(Sum("kilos"), 0, output_field=DecimalField())
        )["t"]
        area = float(ciclo.lote.area_hectareas) or 1

        return Response({
            "ciclo_id": ciclo.id,
            "lote": ciclo.lote.nombre,
            "cosechas": cosechas.count(),
            "kilos_totales": float(total),
            "kilos_por_hectarea": round(float(total) / area, 2),
        })


# Reportes

def filas_historial(ciclo_id=None):
    consulta = Labor.objects.select_related("empleado", "ciclo__lote__cultivo").all()
    if ciclo_id:
        consulta = consulta.filter(ciclo_id=ciclo_id)

    return [
        [
            str(l.fecha_ejecucion or l.fecha_programada),
            l.ciclo.lote.nombre,
            l.ciclo.lote.cultivo.nombre,
            l.tipo,
            l.estado,
            l.empleado.nombre,
            l.producto or "",
            float(l.costo),
        ]
        for l in consulta
    ]


class ReportesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def resumen(self, request):
        return Response({
            "ciclos_activos": Ciclo.objects.filter(estado=EstadoCiclo.ACTIVO).count(),
            "lotes": Lote.objects.filter(activo=True).count(),
            "empleados": Empleado.objects.filter(activo=True).count(),
            "labores_pendientes": Labor.objects.filter(estado=EstadoLabor.PROGRAMADA).count(),
            "kilos_totales": Cosecha.objects.aggregate(
                t=Coalesce(Sum("kilos"), 0, output_field=DecimalField())
            )["t"],
            "costo_total": Labor.objects.aggregate(t=CERO)["t"],
        })

    @action(detail=False, methods=["get"])
    def ciclos(self, request):
        resultado = []

        for ciclo in Ciclo.objects.select_related("lote__cultivo").all():
            resultado.append({
                "ciclo_id": ciclo.id,
                "lote": ciclo.lote.nombre,
                "cultivo": ciclo.lote.cultivo.nombre,
                "estado": ciclo.estado,
                "total_labores": ciclo.labores.count(),
                "costo_total": ciclo.labores.aggregate(t=CERO)["t"],
                "kilos_cosechados": ciclo.cosechas.aggregate(
                    t=Coalesce(Sum("kilos"), 0, output_field=DecimalField())
                )["t"],
            })

        return Response(resultado)

    @action(detail=False, methods=["get"])
    def costos(self, request):
        consulta = Labor.objects.all()
        ciclo_id = request.query_params.get("ciclo_id")
        if ciclo_id:
            consulta = consulta.filter(ciclo_id=ciclo_id)

        agrupado = consulta.values("tipo").annotate(cantidad=Count("id"), costo_total=CERO)
        return Response(list(agrupado))

    @action(detail=False, methods=["get"])
    def historial(self, request):
        filas = filas_historial(request.query_params.get("ciclo_id"))
        return Response([dict(zip(ENCABEZADOS, fila)) for fila in filas])

    # Exportacion opcional (relacion extend del diagrama)

    @action(detail=False, methods=["get"], url_path="exportar/csv",
            permission_classes=[SoloAdministrador])
    def exportar_csv(self, request):
        buffer = io.StringIO()
        escritor = csv.writer(buffer)
        escritor.writerow(ENCABEZADOS)
        escritor.writerows(filas_historial(request.query_params.get("ciclo_id")))

        nombre = f"historial_labores_{date.today()}.csv"
        respuesta = HttpResponse(
            buffer.getvalue().encode("utf-8-sig"), content_type="text/csv"
        )
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return respuesta

    @action(detail=False, methods=["get"], url_path="exportar/excel",
            permission_classes=[SoloAdministrador])
    def exportar_excel(self, request):
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Historial"
        hoja.append(ENCABEZADOS)

        for fila in filas_historial(request.query_params.get("ciclo_id")):
            hoja.append(fila)

        for columna in hoja.columns:
            ancho = max(len(str(c.value or "")) for c in columna) + 2
            hoja.column_dimensions[columna[0].column_letter].width = min(ancho, 40)

        buffer = io.BytesIO()
        libro.save(buffer)

        nombre = f"historial_labores_{date.today()}.xlsx"
        respuesta = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return respuesta


# Comprobacion de que la API responde

@api_view(["GET"])
@permission_classes([AllowAny])
def salud(request):
    return Response({"estado": "ok"})
