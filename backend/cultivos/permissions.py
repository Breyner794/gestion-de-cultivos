# Control de acceso por rol

from rest_framework.permissions import SAFE_METHODS, BasePermission


class SoloAdministrador(BasePermission):
    """Solo el administrador puede entrar."""

    message = "Esta accion es solo para administradores"

    def has_permission(self, request, view):
        return bool(request.user and request.user.es_administrador)


class AdministradorEscribeEmpleadoLee(BasePermission):
    """El empleado puede consultar; solo el administrador modifica."""

    message = "Esta accion es solo para administradores"

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.es_administrador)
