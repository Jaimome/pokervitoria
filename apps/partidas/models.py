import uuid

from django.conf import settings
from django.db import models


class EstadoPartida(models.TextChoices):
    ESPERANDO = "esperando", "Esperando"
    EN_CURSO = "en_curso", "En curso"
    FINALIZADA = "finalizada", "Finalizada"
    CANCELADA = "cancelada", "Cancelada"


class EstadoParticipacion(models.TextChoices):
    UNIDO = "unido", "Unido"
    LISTO = "listo", "Listo"
    JUGANDO = "jugando", "Jugando"
    ELIMINADO = "eliminado", "Eliminado"
    SALIO = "salio", "Salio"


class PartidaPoker(models.Model):
    """
    Una instancia de partida representa el ciclo de vida de una mesa online.

    Aqui guardamos el estado general de la partida. Las rondas de apuestas y la
    resolucion detallada de cartas iran despues en el motor de reglas.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partidas_creadas",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoPartida.choices,
        default=EstadoPartida.ESPERANDO,
    )
    maximo_jugadores = models.PositiveSmallIntegerField(default=6)
    ciega_pequena = models.PositiveIntegerField(default=10)
    ciega_grande = models.PositiveIntegerField(default=20)
    iniciada_en = models.DateTimeField(null=True, blank=True)
    finalizada_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada_en"]
        verbose_name = "partida de poker"
        verbose_name_plural = "partidas de poker"

    def __str__(self) -> str:
        return f"{self.nombre} ({self.get_estado_display()})"

    @property
    def numero_jugadores(self) -> int:
        return self.participaciones.count()

    def obtener_primer_asiento_libre(self) -> int | None:
        asientos_ocupados = set(self.participaciones.values_list("numero_asiento", flat=True))
        for numero_asiento in range(1, self.maximo_jugadores + 1):
            if numero_asiento not in asientos_ocupados:
                return numero_asiento
        return None


class ParticipacionPartida(models.Model):
    """Relacion entre un usuario y una partida concreta."""

    partida = models.ForeignKey(
        PartidaPoker,
        on_delete=models.CASCADE,
        related_name="participaciones",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="participaciones_en_partidas",
    )
    numero_asiento = models.PositiveSmallIntegerField()
    fichas = models.PositiveIntegerField(default=1000)
    estado = models.CharField(
        max_length=20,
        choices=EstadoParticipacion.choices,
        default=EstadoParticipacion.UNIDO,
    )
    unido_en = models.DateTimeField(auto_now_add=True)
    salio_en = models.DateTimeField(null=True, blank=True)
    es_ganador = models.BooleanField(default=False)
    posicion_final = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["numero_asiento"]
        verbose_name = "participacion en partida"
        verbose_name_plural = "participaciones en partida"
        constraints = [
            models.UniqueConstraint(
                fields=["partida", "numero_asiento"],
                name="asiento_unico_por_partida",
            ),
            models.UniqueConstraint(
                fields=["partida", "usuario"],
                name="usuario_unico_por_partida",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.usuario} en {self.partida}"
