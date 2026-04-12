from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from apps.usuarios.forms import FormularioRegistroUsuario


class VistaRegistroUsuario(CreateView):
    """Permite crear una cuenta y autenticarla en el mismo flujo."""

    form_class = FormularioRegistroUsuario
    template_name = "usuarios/registro.html"
    success_url = reverse_lazy("usuarios:perfil")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("usuarios:perfil")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class VistaPerfil(LoginRequiredMixin, TemplateView):
    """Pagina minima para comprobar que la sesion esta activa."""

    template_name = "usuarios/perfil.html"
