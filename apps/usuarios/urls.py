from django.urls import path

from apps.usuarios.views import (
    VistaBorrarCuenta,
    VistaCerrarSesion,
    VistaInicioSesion,
    VistaPerfil,
    VistaRegistroUsuario,
)


app_name = "usuarios"

urlpatterns = [
    path("registro/", VistaRegistroUsuario.as_view(), name="registro"),
    path("iniciar-sesion/", VistaInicioSesion.as_view(), name="iniciar_sesion"),
    path("cerrar-sesion/", VistaCerrarSesion.as_view(), name="cerrar_sesion"),
    path("perfil/", VistaPerfil.as_view(), name="perfil"),
    path("borrar-cuenta/", VistaBorrarCuenta.as_view(), name="borrar_cuenta"),
]
