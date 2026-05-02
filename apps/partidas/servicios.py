from random import SystemRandom

from django.utils import timezone

from apps.partidas.evaluador import comparar_manos
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
ORDEN_FASES = [EstadoMano.PREFLOP, EstadoMano.FLOP, EstadoMano.TURN, EstadoMano.RIVER]


def iniciar_mano_inicial(partida: PartidaPoker) -> ManoPoker:
    """
    Crea la primera mano activa de la partida, reparte cartas privadas y publica
    las ciegas iniciales.
    """

    participantes = list(
        partida.participaciones.exclude(estado=EstadoParticipacion.SALIO)
        .select_related("usuario")
        .order_by("numero_asiento")
    )
    if len(participantes) < 2:
        raise ValueError("No se puede iniciar una partida con menos de dos jugadores.")

    if partida.manos.filter(estado__in=ORDEN_FASES).exists():
        raise ValueError("La partida ya tiene una mano activa.")

    mazo = [f"{valor}{palo}" for palo in PALOS_CARTAS for valor in VALORES_CARTAS]
    SystemRandom().shuffle(mazo)

    turno_inicial = participantes[0] if len(participantes) == 2 else participantes[2]
    mano = ManoPoker.objects.create(
        partida=partida,
        numero_mano=partida.manos.count() + 1,
        estado=EstadoMano.PREFLOP,
        turno_actual=turno_inicial,
        incremento_minimo_subida=partida.ciega_grande,
    )

    cartas_a_crear = []
    for participacion in participantes:
        participacion.estado = EstadoParticipacion.JUGANDO
        participacion.activa_en_mano = True
        participacion.apuesta_en_ronda = 0
        participacion.ha_actuado_en_ronda = False
        participacion.save(
            update_fields=[
                "estado",
                "activa_en_mano",
                "apuesta_en_ronda",
                "ha_actuado_en_ronda",
            ]
        )
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
    _publicar_ciegas(partida, mano, participantes)
    mano.mazo_restante = ",".join(mazo)
    mano.save(
        update_fields=[
            "bote_total",
            "apuesta_actual_ronda",
            "turno_actual",
            "mazo_restante",
            "incremento_minimo_subida",
        ]
    )
    partida.iniciar_partida()
    return mano


def ejecutar_accion(
    mano: ManoPoker,
    participacion: ParticipacionPartida,
    tipo: str,
    objetivo_subida: int | None = None,
) -> None:
    """Ejecuta una accion de la ronda actual y actualiza turno o fase."""

    if mano.estado not in ORDEN_FASES:
        raise ValueError("La mano actual no admite acciones.")

    if mano.turno_actual_id != participacion.id:
        raise ValueError("No es el turno de este jugador.")

    if not participacion.activa_en_mano:
        raise ValueError("Este jugador ya no sigue activo en la mano.")

    if tipo == TipoAccion.PASAR:
        if participacion.apuesta_en_ronda != mano.apuesta_actual_ronda:
            raise ValueError("No puedes pasar mientras tengas fichas por igualar.")
        participacion.ha_actuado_en_ronda = True
        participacion.save(update_fields=["ha_actuado_en_ronda"])

    elif tipo == TipoAccion.IGUALAR:
        diferencia = mano.apuesta_actual_ronda - participacion.apuesta_en_ronda
        if diferencia <= 0:
            raise ValueError("No tienes ninguna apuesta pendiente por igualar.")
        if participacion.fichas < diferencia:
            raise ValueError("No tienes fichas suficientes para igualar.")
        participacion.fichas -= diferencia
        participacion.apuesta_en_ronda += diferencia
        participacion.ha_actuado_en_ronda = True
        participacion.save(update_fields=["fichas", "apuesta_en_ronda", "ha_actuado_en_ronda"])
        mano.bote_total += diferencia
        mano.save(update_fields=["bote_total"])

    elif tipo == TipoAccion.SUBIR:
        if objetivo_subida is None:
            raise ValueError("Debes indicar a cuanto quieres subir.")
        if objetivo_subida <= mano.apuesta_actual_ronda:
            raise ValueError("La subida debe superar la apuesta actual de la ronda.")

        minimo_objetivo = mano.apuesta_actual_ronda + mano.incremento_minimo_subida
        if objetivo_subida < minimo_objetivo:
            raise ValueError(
                f"La subida minima actual es hasta {minimo_objetivo} fichas."
            )

        diferencia = objetivo_subida - participacion.apuesta_en_ronda
        if diferencia <= 0:
            raise ValueError("La subida indicada no modifica tu apuesta actual.")
        if participacion.fichas < diferencia:
            raise ValueError("No tienes fichas suficientes para realizar esa subida.")

        apuesta_previa = mano.apuesta_actual_ronda
        incremento_realizado = objetivo_subida - apuesta_previa

        participacion.fichas -= diferencia
        participacion.apuesta_en_ronda = objetivo_subida
        participacion.ha_actuado_en_ronda = True
        participacion.save(update_fields=["fichas", "apuesta_en_ronda", "ha_actuado_en_ronda"])

        for rival in mano.participantes_activos().exclude(id=participacion.id):
            rival.ha_actuado_en_ronda = False
            rival.save(update_fields=["ha_actuado_en_ronda"])

        mano.bote_total += diferencia
        mano.apuesta_actual_ronda = objetivo_subida
        mano.incremento_minimo_subida = incremento_realizado
        mano.save(
            update_fields=[
                "bote_total",
                "apuesta_actual_ronda",
                "incremento_minimo_subida",
            ]
        )

    elif tipo == TipoAccion.RETIRARSE:
        participacion.activa_en_mano = False
        participacion.ha_actuado_en_ronda = True
        participacion.save(update_fields=["activa_en_mano", "ha_actuado_en_ronda"])
    else:
        raise ValueError("La accion indicada no esta soportada todavia.")

    orden_siguiente = mano.acciones.count() + 1
    AccionMano.objects.create(
        mano=mano,
        participacion=participacion,
        tipo=tipo,
        orden=orden_siguiente,
    )

    participantes_activos = list(mano.participantes_activos())
    if len(participantes_activos) == 1:
        ganador = participantes_activos[0]
        _cerrar_mano_por_ganador_directo(
            mano,
            ganador,
            "Gana por retirada del resto de jugadores",
        )
        return

    if _ronda_completada(mano):
        _avanzar_fase(mano)
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

    mano = partida.manos.filter(estado__in=ORDEN_FASES).order_by("-creada_en").first()
    if mano is None:
        return

    participantes_activos = list(mano.participantes_activos())
    if len(participantes_activos) == 1:
        ganador = participantes_activos[0]
        _cerrar_mano_por_ganador_directo(
            mano,
            ganador,
            "Gana por retirada del resto de jugadores",
        )
        return

    if mano.turno_actual_id == participacion.id:
        mano.turno_actual = obtener_siguiente_turno(mano, participacion)
        mano.save(update_fields=["turno_actual"])


def _publicar_ciegas(
    partida: PartidaPoker,
    mano: ManoPoker,
    participantes: list[ParticipacionPartida],
) -> None:
    ciega_pequena = participantes[0]
    ciega_grande = participantes[1]

    _cobrar_apuesta(partida.ciega_pequena, ciega_pequena)
    _cobrar_apuesta(partida.ciega_grande, ciega_grande)

    mano.bote_total = partida.ciega_pequena + partida.ciega_grande
    mano.apuesta_actual_ronda = partida.ciega_grande
    mano.incremento_minimo_subida = partida.ciega_grande


def _cobrar_apuesta(cantidad: int, participacion: ParticipacionPartida) -> None:
    if participacion.fichas < cantidad:
        raise ValueError("Un jugador no tiene fichas suficientes para publicar las ciegas.")
    participacion.fichas -= cantidad
    participacion.apuesta_en_ronda = cantidad
    participacion.save(update_fields=["fichas", "apuesta_en_ronda"])


def _ronda_completada(mano: ManoPoker) -> bool:
    participantes_activos = list(mano.participantes_activos())
    if not participantes_activos:
        return False

    return all(
        participacion.ha_actuado_en_ronda
        and participacion.apuesta_en_ronda == mano.apuesta_actual_ronda
        for participacion in participantes_activos
    )


def _avanzar_fase(mano: ManoPoker) -> None:
    participantes_activos = list(mano.participantes_activos())

    if mano.estado == EstadoMano.PREFLOP:
        mano.estado = EstadoMano.FLOP
        _repartir_cartas_comunitarias(mano, 3)
    elif mano.estado == EstadoMano.FLOP:
        mano.estado = EstadoMano.TURN
        _repartir_cartas_comunitarias(mano, 1)
    elif mano.estado == EstadoMano.TURN:
        mano.estado = EstadoMano.RIVER
        _repartir_cartas_comunitarias(mano, 1)
    elif mano.estado == EstadoMano.RIVER:
        _resolver_showdown(mano)
        return

    for participacion in participantes_activos:
        participacion.apuesta_en_ronda = 0
        participacion.ha_actuado_en_ronda = False
        participacion.save(update_fields=["apuesta_en_ronda", "ha_actuado_en_ronda"])

    mano.apuesta_actual_ronda = 0
    mano.incremento_minimo_subida = mano.partida.ciega_grande
    mano.turno_actual = participantes_activos[0] if participantes_activos else None
    mano.save(
        update_fields=[
            "estado",
            "cartas_comunitarias",
            "mazo_restante",
            "apuesta_actual_ronda",
            "incremento_minimo_subida",
            "turno_actual",
        ]
    )


def _repartir_cartas_comunitarias(mano: ManoPoker, cantidad: int) -> None:
    mazo = [carta for carta in mano.mazo_restante.split(",") if carta]
    cartas_actuales = mano.cartas_comunitarias_visibles()
    nuevas_cartas = []
    for _ in range(cantidad):
        nuevas_cartas.append(mazo.pop())
    mano.cartas_comunitarias = ",".join(cartas_actuales + nuevas_cartas)
    mano.mazo_restante = ",".join(mazo)


def _resolver_showdown(mano: ManoPoker) -> None:
    participantes_activos = list(mano.participantes_activos().select_related("usuario"))
    cartas_comunitarias = mano.cartas_comunitarias_visibles()
    cartas_por_jugador = {}

    for participacion in participantes_activos:
        cartas_privadas = list(
            mano.cartas_privadas.filter(participacion=participacion).values_list("codigo", flat=True)
        )
        cartas_por_jugador[participacion] = cartas_privadas + cartas_comunitarias

    resultados_ganadores = comparar_manos(cartas_por_jugador)
    ganadores = [resultado["participacion"] for resultado in resultados_ganadores]
    descripcion = resultados_ganadores[0]["nombre"]

    _repartir_bote(mano.bote_total, ganadores)

    mano.estado = EstadoMano.FINALIZADA
    mano.turno_actual = None
    mano.ganador = ganadores[0] if len(ganadores) == 1 else None
    mano.descripcion_resultado = _construir_descripcion_showdown(ganadores, descripcion)
    mano.save(update_fields=["estado", "turno_actual", "ganador", "descripcion_resultado"])
    mano.ganadores.set(ganadores)


def _cerrar_mano_por_ganador_directo(
    mano: ManoPoker,
    ganador: ParticipacionPartida,
    descripcion_resultado: str,
) -> None:
    _repartir_bote(mano.bote_total, [ganador])
    mano.estado = EstadoMano.FINALIZADA
    mano.turno_actual = None
    mano.ganador = ganador
    mano.descripcion_resultado = descripcion_resultado
    mano.save(update_fields=["estado", "turno_actual", "ganador", "descripcion_resultado"])
    mano.ganadores.set([ganador])


def _repartir_bote(bote_total: int, ganadores: list[ParticipacionPartida]) -> None:
    if not ganadores or bote_total <= 0:
        return

    ganadores_ordenados = sorted(ganadores, key=lambda participacion: participacion.numero_asiento)
    cantidad_base = bote_total // len(ganadores_ordenados)
    resto = bote_total % len(ganadores_ordenados)

    for indice, ganador in enumerate(ganadores_ordenados):
        extra = 1 if indice < resto else 0
        ganador.fichas += cantidad_base + extra
        ganador.save(update_fields=["fichas"])


def _construir_descripcion_showdown(
    ganadores: list[ParticipacionPartida],
    nombre_combinacion: str,
) -> str:
    if len(ganadores) == 1:
        return f"{ganadores[0].usuario} gana con {nombre_combinacion.lower()}"

    nombres = ", ".join(str(ganador.usuario) for ganador in ganadores)
    return f"Empate entre {nombres} con {nombre_combinacion.lower()}"
