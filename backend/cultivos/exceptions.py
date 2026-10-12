# Deja todos los errores con la misma forma: {"detail": "mensaje"}

from rest_framework.views import exception_handler


def primer_mensaje(datos):
    if isinstance(datos, str):
        return datos
    if isinstance(datos, list) and datos:
        return primer_mensaje(datos[0])
    if isinstance(datos, dict):
        if "detail" in datos:
            return primer_mensaje(datos["detail"])
        for campo, valor in datos.items():
            mensaje = primer_mensaje(valor)
            if campo == "non_field_errors":
                return mensaje
            return f"{campo}: {mensaje}"
    return "Ocurrio un error inesperado"


def manejador(excepcion, contexto):
    respuesta = exception_handler(excepcion, contexto)

    if respuesta is not None:
        respuesta.data = {"detail": primer_mensaje(respuesta.data)}

    return respuesta
