from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.views.generic import TemplateView


def contar_usuarios_conectados() -> int:
    """Cuenta usuarios autenticados con una sesion todavia activa."""

    ahora = timezone.now()
    sesiones = Session.objects.filter(expire_date__gte=ahora)
    usuarios = set()
    for sesion in sesiones:
        datos = sesion.get_decoded()
        usuario_id = datos.get("_auth_user_id")
        if usuario_id:
            usuarios.add(usuario_id)
    return len(usuarios)


class VistaInicio(TemplateView):
    """Pantalla de inicio publica o privada segun el estado de sesion."""

    template_name = "pages/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usuarios_conectados"] = contar_usuarios_conectados()
        return context


class VistaReglasPoker(LoginRequiredMixin, TemplateView):
    """Pantalla informativa con reglas basicas de Texas Hold'em."""

    template_name = "pages/reglas.html"
