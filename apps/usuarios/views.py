from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from apps.usuarios.forms import FormularioInicioSesion, FormularioRegistroUsuario


class VistaRegistroUsuario(CreateView):
    """Permite crear una cuenta y autenticarla en el mismo flujo."""

    form_class = FormularioRegistroUsuario
    template_name = "usuarios/registro.html"
    success_url = reverse_lazy("nucleo:inicio")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("nucleo:inicio")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Cuenta creada correctamente.")
        return response


class VistaInicioSesion(LoginView):
    """Pantalla de acceso adaptada al flujo principal del proyecto."""

    authentication_form = FormularioInicioSesion
    template_name = "usuarios/iniciar_sesion.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("nucleo:inicio")


class VistaPerfil(LoginRequiredMixin, TemplateView):
    """Pantalla de perfil del usuario autenticado."""

    template_name = "usuarios/perfil.html"


class VistaCerrarSesion(LoginRequiredMixin, View):
    """Cierra la sesión del usuario y vuelve a la portada pública."""

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Sesión cerrada correctamente.")
        return redirect("nucleo:inicio")


class VistaBorrarCuenta(LoginRequiredMixin, View):
    """Borra la cuenta del usuario autenticado."""

    def post(self, request, *args, **kwargs):
        usuario = request.user
        logout(request)
        usuario.delete()
        messages.success(request, "La cuenta se ha borrado correctamente.")
        return redirect("nucleo:inicio")
