from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.usuarios.models import Usuario


class VistaRanking(LoginRequiredMixin, ListView):
    """Muestra la lista completa de jugadores ordenados por saldo total."""

    model = Usuario
    template_name = "clasificacion/ranking.html"
    context_object_name = "jugadores"

    def get_queryset(self):
        return Usuario.objects.order_by("-saldo_total", "username")
