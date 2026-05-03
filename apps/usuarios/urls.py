from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from apps.usuarios.forms import FormularioInicioSesion
from apps.usuarios.views import VistaPerfil, VistaRegistroUsuario


app_name = "usuarios"

urlpatterns = [
    path("registro/", VistaRegistroUsuario.as_view(), name="registro"),
    path(
        "iniciar-sesion/",
        LoginView.as_view(
            authentication_form=FormularioInicioSesion,
            template_name="usuarios/iniciar_sesion.html",
            redirect_authenticated_user=True,
        ),
        name="iniciar_sesion",
    ),
    path("cerrar-sesion/", LogoutView.as_view(), name="cerrar_sesion"),
    path("perfil/", VistaPerfil.as_view(), name="perfil"),
]
