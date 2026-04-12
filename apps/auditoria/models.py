from django.conf import settings
from django.db import models


class EventoAuditoria(models.Model):
    """Registro generico de eventos para seguridad y trazabilidad del juego."""

    categoria = models.CharField(max_length=50)
    accion = models.CharField(max_length=100)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_auditoria",
    )
    referencia_partida = models.CharField(max_length=64, blank=True)
    detalles = models.JSONField(default=dict, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en"]
        verbose_name = "evento de auditoria"
        verbose_name_plural = "eventos de auditoria"

    def __str__(self) -> str:
        objetivo = self.usuario or "anonimo"
        return f"{self.categoria}:{self.accion} por {objetivo}"
