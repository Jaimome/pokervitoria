from random import SystemRandom

from apps.partidas.models import (
    CartaPrivada,
    EstadoMano,
    EstadoParticipacion,
    ManoPoker,
    ParticipacionPartida,
    PartidaPoker,
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
    )

    cartas_a_crear = []
    for participacion in participantes:
        participacion.estado = EstadoParticipacion.JUGANDO
        participacion.save(update_fields=["estado"])
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
