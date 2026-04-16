import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


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


class EstadoMano(models.TextChoices):
    PREPARANDO = "preparando", "Preparando"
    PREFLOP = "preflop", "Preflop"
    FLOP = "flop", "Flop"
    TURN = "turn", "Turn"
    RIVER = "river", "River"
    FINALIZADA = "finalizada", "Finalizada"


class TipoAccion(models.TextChoices):
    PASAR = "pasar", "Pasar"
    IGUALAR = "igualar", "Igualar"
    SUBIR = "subir", "Subir"
    RETIRARSE = "retirarse", "Retirarse"


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
        return self.participaciones.exclude(estado=EstadoParticipacion.SALIO).count()

    def obtener_primer_asiento_libre(self) -> int | None:
        asientos_ocupados = set(
            self.participaciones.exclude(estado=EstadoParticipacion.SALIO).values_list(
                "numero_asiento", flat=True
            )
        )
        for numero_asiento in range(1, self.maximo_jugadores + 1):
            if numero_asiento not in asientos_ocupados:
                return numero_asiento
        return None

    def puede_iniciarse(self) -> bool:
        return self.numero_jugadores >= 2 and not self.manos.exclude(
            estado=EstadoMano.FINALIZADA
        ).exists()

    def iniciar_partida(self) -> None:
        self.estado = EstadoPartida.EN_CURSO
        if self.iniciada_en is None:
            self.iniciada_en = timezone.now()
        self.save(update_fields=["estado", "iniciada_en", "actualizada_en"])


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
    activa_en_mano = models.BooleanField(default=False)
    apuesta_en_ronda = models.PositiveIntegerField(default=0)
    ha_actuado_en_ronda = models.BooleanField(default=False)
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


class ManoPoker(models.Model):
    """Representa una mano concreta dentro de una partida."""

    partida = models.ForeignKey(
        PartidaPoker,
        on_delete=models.CASCADE,
        related_name="manos",
    )
    numero_mano = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoMano.choices,
        default=EstadoMano.PREPARANDO,
    )
    turno_actual = models.ForeignKey(
        ParticipacionPartida,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="turnos_actuales",
    )
    ganador = models.ForeignKey(
        ParticipacionPartida,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manos_ganadas_provisionalmente",
    )
    bote_total = models.PositiveIntegerField(default=0)
    apuesta_actual_ronda = models.PositiveIntegerField(default=0)
    incremento_minimo_subida = models.PositiveIntegerField(default=0)
    cartas_comunitarias = models.CharField(max_length=50, blank=True)
    mazo_restante = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en"]
        verbose_name = "mano de poker"
        verbose_name_plural = "manos de poker"
        constraints = [
            models.UniqueConstraint(
                fields=["partida", "numero_mano"],
                name="numero_mano_unico_por_partida",
            )
        ]

    def __str__(self) -> str:
        return f"Mano {self.numero_mano} de {self.partida.nombre}"

    def participantes_activos(self):
        return self.partida.participaciones.filter(activa_en_mano=True).order_by("numero_asiento")

    def cartas_comunitarias_visibles(self) -> list[str]:
        if not self.cartas_comunitarias:
            return []
        return [carta for carta in self.cartas_comunitarias.split(",") if carta]


class CartaPrivada(models.Model):
    """Carta privada repartida a un jugador en una mano concreta."""

    mano = models.ForeignKey(
        ManoPoker,
        on_delete=models.CASCADE,
        related_name="cartas_privadas",
    )
    participacion = models.ForeignKey(
        ParticipacionPartida,
        on_delete=models.CASCADE,
        related_name="cartas_privadas",
    )
    orden = models.PositiveSmallIntegerField()
    codigo = models.CharField(max_length=3)

    class Meta:
        ordering = ["orden"]
        verbose_name = "carta privada"
        verbose_name_plural = "cartas privadas"
        constraints = [
            models.UniqueConstraint(
                fields=["mano", "participacion", "orden"],
                name="carta_privada_unica_por_orden",
            )
        ]

    def __str__(self) -> str:
        return f"{self.codigo} para {self.participacion.usuario}"

    @property
    def codigo_visible(self) -> str:
        """Devuelve el codigo corto de la carta con notacion en castellano."""

        return self.codigo


class AccionMano(models.Model):
    """Accion realizada por un jugador durante una mano."""

    mano = models.ForeignKey(
        ManoPoker,
        on_delete=models.CASCADE,
        related_name="acciones",
    )
    participacion = models.ForeignKey(
        ParticipacionPartida,
        on_delete=models.CASCADE,
        related_name="acciones_en_manos",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoAccion.choices,
    )
    orden = models.PositiveIntegerField()
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "creada_en"]
        verbose_name = "accion de mano"
        verbose_name_plural = "acciones de mano"
        constraints = [
            models.UniqueConstraint(
                fields=["mano", "orden"],
                name="orden_unico_accion_por_mano",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} de {self.participacion.usuario}"
