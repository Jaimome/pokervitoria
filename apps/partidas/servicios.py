from random import SystemRandom
from django.utils import timezone

from apps.partidas.models import (
    AccionMano,
    CartaPrivada,
    EstadoMano,
    EstadoParticipacion,
    ManoPoker,
    ParticipacionPartida,
    PartidaPoker,
    TipoAccion,
)


VALORES_CARTAS = ("A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2")
PALOS_CARTAS = ("P", "C", "D", "T")


def iniciar_mano_inicial(partida: PartidaPoker) -> ManoPoker:
    """
    Crea la primera mano activa de la partida y reparte dos cartas privadas
    a cada participante.
    """

    participantes = list(partida.participaciones.select_related("usuario").order_by("numero_asiento"))
    if len(participantes) < 2:
        raise ValueError("No se puede iniciar una partida con menos de dos jugadores.")

    if partida.manos.filter(estado__in=[EstadoMano.PREPARANDO, EstadoMano.PREFLOP]).exists():
        raise ValueError("La partida ya tiene una mano activa.")

    mazo = [f"{valor}{palo}" for palo in PALOS_CARTAS for valor in VALORES_CARTAS]
    SystemRandom().shuffle(mazo)

    mano = ManoPoker.objects.create(
        partida=partida,
        numero_mano=partida.manos.count() + 1,
        estado=EstadoMano.PREFLOP,
        turno_actual=participantes[0],
    )

    cartas_a_crear = []
    for participacion in participantes:
        participacion.estado = EstadoParticipacion.JUGANDO
        participacion.activa_en_mano = True
        participacion.save(update_fields=["estado", "activa_en_mano"])
        for orden in (1, 2):
            cartas_a_crear.append(
                CartaPrivada(
                    mano=mano,
                    participacion=participacion,
                    orden=orden,
                    codigo=mazo.pop(),
                )
            )

    CartaPrivada.objects.bulk_create(cartas_a_crear)
    partida.iniciar_partida()
    return mano


def ejecutar_accion(mano: ManoPoker, participacion: ParticipacionPartida, tipo: str) -> None:
    """Ejecuta una accion minima de preflop y actualiza el turno."""

    if mano.estado != EstadoMano.PREFLOP:
        raise ValueError("La mano actual no admite acciones.")

    if mano.turno_actual_id != participacion.id:
        raise ValueError("No es el turno de este jugador.")

    if not participacion.activa_en_mano:
        raise ValueError("Este jugador ya no sigue activo en la mano.")

    orden_siguiente = mano.acciones.count() + 1
    AccionMano.objects.create(
        mano=mano,
        participacion=participacion,
        tipo=tipo,
        orden=orden_siguiente,
    )

    if tipo == TipoAccion.RETIRARSE:
        participacion.activa_en_mano = False
        participacion.save(update_fields=["activa_en_mano"])

    participantes_activos = list(mano.participantes_activos())
    if len(participantes_activos) == 1:
        ganador = participantes_activos[0]
        mano.estado = EstadoMano.FINALIZADA
        mano.turno_actual = None
        mano.ganador = ganador
        mano.save(update_fields=["estado", "turno_actual", "ganador"])
        return

    mano.turno_actual = obtener_siguiente_turno(mano, participacion)
    mano.save(update_fields=["turno_actual"])


def obtener_siguiente_turno(
    mano: ManoPoker,
    participacion_actual: ParticipacionPartida,
) -> ParticipacionPartida:
    """Devuelve el siguiente participante activo por orden de asiento."""

    participantes_activos = list(mano.participantes_activos())
    if not participantes_activos:
        raise ValueError("No quedan participantes activos en la mano.")

    for participacion in participantes_activos:
        if participacion.numero_asiento > participacion_actual.numero_asiento:
            return participacion

    return participantes_activos[0]


def abandonar_partida(partida: PartidaPoker, participacion: ParticipacionPartida) -> None:
    """Permite a un jugador salir de una partida sin bloquear el testing."""

    participacion.estado = EstadoParticipacion.SALIO
    participacion.activa_en_mano = False
    participacion.salio_en = timezone.now()
    participacion.save(update_fields=["estado", "activa_en_mano", "salio_en"])

    mano = partida.manos.filter(estado=EstadoMano.PREFLOP).order_by("-creada_en").first()
    if mano is None:
        return

    participantes_activos = list(mano.participantes_activos())
    if len(participantes_activos) == 1:
        ganador = participantes_activos[0]
        mano.estado = EstadoMano.FINALIZADA
        mano.turno_actual = None
        mano.ganador = ganador
        mano.save(update_fields=["estado", "turno_actual", "ganador"])
        return

    if mano.turno_actual_id == participacion.id:
        mano.turno_actual = obtener_siguiente_turno(mano, participacion)
        mano.save(update_fields=["turno_actual"])
