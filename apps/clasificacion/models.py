from django.conf import settings
from django.db import models


class EstadisticasJugador(models.Model):
    """
    Estadisticas agregadas para ranking y perfil.

    Estos contadores podran recalcularse mas adelante a partir de las partidas
    finalizadas si fuera necesario.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="estadisticas",
    )
    partidas_jugadas = models.PositiveIntegerField(default=0)
    victorias = models.PositiveIntegerField(default=0)
    derrotas = models.PositiveIntegerField(default=0)
    puntos = models.IntegerField(default=0)
    racha_actual = models.IntegerField(default=0)
    mejor_racha = models.PositiveIntegerField(default=0)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "estadisticas de jugador"
        verbose_name_plural = "estadisticas de jugadores"
        ordering = ["-puntos", "-victorias", "usuario__username"]

    def __str__(self) -> str:
        return f"Estadisticas de {self.usuario}"
