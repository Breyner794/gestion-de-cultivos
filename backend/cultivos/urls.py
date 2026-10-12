# Rutas de la API

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cultivos import views

router = DefaultRouter(trailing_slash=False)
router.register("empleados", views.EmpleadoViewSet, basename="empleados")
router.register("cultivos", views.CultivoViewSet, basename="cultivos")
router.register("lotes", views.LoteViewSet, basename="lotes")
router.register("ciclos", views.CicloViewSet, basename="ciclos")
router.register("labores", views.LaborViewSet, basename="labores")
router.register("cosechas", views.CosechaViewSet, basename="cosechas")
router.register("reportes", views.ReportesViewSet, basename="reportes")
router.register("auth/usuarios", views.UsuarioViewSet, basename="usuarios")

urlpatterns = [
    path("auth/login", views.LoginView.as_view()),
    path("auth/yo", views.mi_perfil),
    path("salud", views.salud),
    path("", include(router.urls)),
]
