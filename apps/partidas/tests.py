from django.test import TestCase
from django.urls import reverse

from apps.partidas.models import (
    AccionMano,
    CartaPrivada,
    EstadoMano,
    EstadoPartida,
    EstadoParticipacion,
    ManoPoker,
    ParticipacionPartida,
    PartidaPoker,
)
from apps.usuarios.models import Usuario


class FlujoPartidasTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="jugador1",
            password="ClaveSegura123!",
        )
        self.segundo_usuario = Usuario.objects.create_user(
            username="jugador2",
            password="ClaveSegura123!",
        )
        self.tercer_usuario = Usuario.objects.create_user(
            username="jugador3",
            password="ClaveSegura123!",
        )
        self.client.login(username="jugador1", password="ClaveSegura123!")

    def test_un_usuario_autenticado_puede_crear_una_partida(self):
        response = self.client.post(
            reverse("partidas:crear"),
            data={
                "nombre": "Mesa de prueba",
                "maximo_jugadores": 4,
                "ciega_pequena": 10,
                "ciega_grande": 20,
            },
        )

        partida = PartidaPoker.objects.get(nombre="Mesa de prueba")
        self.assertRedirects(response, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        self.assertEqual(partida.creador, self.usuario)

    def test_un_usuario_puede_unirse_a_una_partida(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa abierta",
            maximo_jugadores=4,
            ciega_pequena=10,
            ciega_grande=20,
        )

        response = self.client.post(reverse("partidas:unirse", kwargs={"pk": partida.pk}))

        self.assertRedirects(response, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        self.assertTrue(
            ParticipacionPartida.objects.filter(partida=partida, usuario=self.usuario).exists()
        )

    def test_se_publican_ciegas_al_iniciar_la_partida(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa activa",
            maximo_jugadores=4,
            ciega_pequena=10,
            ciega_grande=20,
        )
        p1 = ParticipacionPartida.objects.create(partida=partida, usuario=self.usuario, numero_asiento=1)
        p2 = ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.segundo_usuario,
            numero_asiento=2,
        )

        response = self.client.post(reverse("partidas:iniciar", kwargs={"pk": partida.pk}))

        self.assertRedirects(response, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        partida.refresh_from_db()
        p1.refresh_from_db()
        p2.refresh_from_db()
        mano = ManoPoker.objects.get(partida=partida)
        self.assertEqual(partida.estado, EstadoPartida.EN_CURSO)
        self.assertEqual(mano.estado, EstadoMano.PREFLOP)
        self.assertEqual(mano.bote_total, 30)
        self.assertEqual(mano.apuesta_actual_ronda, 20)
        self.assertEqual(p1.fichas, 990)
        self.assertEqual(p2.fichas, 980)
        self.assertEqual(p1.apuesta_en_ronda, 10)
        self.assertEqual(p2.apuesta_en_ronda, 20)
        self.assertEqual(mano.turno_actual.usuario, self.usuario)
        self.assertEqual(
            CartaPrivada.objects.filter(mano=mano, participacion__usuario=self.usuario).count(),
            2,
        )

    def test_igualar_pasa_el_turno_a_la_ciega_grande_y_cierra_preflop_tras_pasar(self):
        partida, mano, participacion_1, participacion_2 = self._crear_partida_iniciada()

        response_1 = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "igualar"},
        )

        self.assertRedirects(response_1, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        mano.refresh_from_db()
        participacion_1.refresh_from_db()
        participacion_2.refresh_from_db()
        self.assertEqual(mano.estado, EstadoMano.PREFLOP)
        self.assertEqual(mano.turno_actual, participacion_2)
        self.assertEqual(mano.bote_total, 40)
        self.assertEqual(participacion_1.apuesta_en_ronda, 20)
        self.assertEqual(participacion_2.apuesta_en_ronda, 20)

        self.client.logout()
        self.client.login(username="jugador2", password="ClaveSegura123!")
        response_2 = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "pasar"},
        )

        self.assertRedirects(response_2, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        mano.refresh_from_db()
        participacion_1.refresh_from_db()
        participacion_2.refresh_from_db()
        self.assertEqual(mano.estado, EstadoMano.FLOP)
        self.assertEqual(len(mano.cartas_comunitarias_visibles()), 3)
        self.assertEqual(mano.bote_total, 40)
        self.assertEqual(mano.apuesta_actual_ronda, 0)
        self.assertEqual(mano.turno_actual, participacion_1)
        self.assertEqual(participacion_1.apuesta_en_ronda, 0)
        self.assertEqual(participacion_2.apuesta_en_ronda, 0)

    def test_pasar_en_flop_avanza_el_turno_y_cierra_la_ronda(self):
        partida, mano, participacion_1, participacion_2 = self._crear_partida_iniciada()
        self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "igualar"},
        )
        self.client.logout()
        self.client.login(username="jugador2", password="ClaveSegura123!")
        self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "pasar"},
        )
        self.client.logout()
        self.client.login(username="jugador1", password="ClaveSegura123!")

        response_1 = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "pasar"},
        )
        self.assertRedirects(response_1, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        mano.refresh_from_db()
        self.assertEqual(mano.turno_actual, participacion_2)

        self.client.logout()
        self.client.login(username="jugador2", password="ClaveSegura123!")
        response_2 = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "pasar"},
        )
        self.assertRedirects(response_2, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        mano.refresh_from_db()
        self.assertEqual(mano.estado, EstadoMano.TURN)
        self.assertEqual(len(mano.cartas_comunitarias_visibles()), 4)

    def test_retirarse_deja_un_ganador_provisional_si_solo_queda_un_jugador(self):
        partida, mano, participacion_1, participacion_2 = self._crear_partida_iniciada()

        response = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "retirarse"},
        )

        self.assertRedirects(response, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        mano.refresh_from_db()
        participacion_1.refresh_from_db()
        self.assertEqual(mano.estado, EstadoMano.FINALIZADA)
        self.assertEqual(mano.ganador, participacion_2)
        self.assertFalse(participacion_1.activa_en_mano)
        self.assertEqual(
            AccionMano.objects.filter(
                mano=mano,
                participacion=participacion_1,
                tipo="retirarse",
            ).count(),
            1,
        )

    def test_un_usuario_puede_abandonar_una_partida_y_salir_del_listado_activo(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa para salir",
            maximo_jugadores=4,
            ciega_pequena=10,
            ciega_grande=20,
        )
        participacion = ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.usuario,
            numero_asiento=1,
            estado=EstadoParticipacion.UNIDO,
        )

        response = self.client.post(reverse("partidas:abandonar", kwargs={"pk": partida.pk}))

        self.assertRedirects(response, reverse("partidas:lista"))
        participacion.refresh_from_db()
        self.assertEqual(participacion.estado, EstadoParticipacion.SALIO)
        self.assertEqual(partida.numero_jugadores, 0)

    def test_abandonar_la_partida_si_es_tu_turno_pasa_el_turno_al_siguiente(self):
        partida, mano, participacion_1, participacion_2 = self._crear_partida_iniciada()

        response = self.client.post(reverse("partidas:abandonar", kwargs={"pk": partida.pk}))

        self.assertRedirects(response, reverse("partidas:lista"))
        mano.refresh_from_db()
        participacion_1.refresh_from_db()
        self.assertEqual(participacion_1.estado, EstadoParticipacion.SALIO)
        self.assertEqual(mano.ganador, participacion_2)
        self.assertEqual(mano.estado, EstadoMano.FINALIZADA)

    def test_un_usuario_puede_volver_a_entrar_tras_haber_salido(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa retorno",
            maximo_jugadores=4,
            ciega_pequena=10,
            ciega_grande=20,
        )
        participacion = ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.usuario,
            numero_asiento=1,
            estado=EstadoParticipacion.SALIO,
        )

        response = self.client.post(reverse("partidas:unirse", kwargs={"pk": partida.pk}))

        self.assertRedirects(response, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        participacion.refresh_from_db()
        self.assertEqual(participacion.estado, EstadoParticipacion.UNIDO)
        self.assertEqual(
            ParticipacionPartida.objects.filter(partida=partida, usuario=self.usuario).count(),
            1,
        )

    def _crear_partida_iniciada(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa activa",
            maximo_jugadores=4,
            ciega_pequena=10,
            ciega_grande=20,
        )
        participacion_1 = ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.usuario,
            numero_asiento=1,
            estado=EstadoParticipacion.UNIDO,
        )
        participacion_2 = ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.segundo_usuario,
            numero_asiento=2,
            estado=EstadoParticipacion.UNIDO,
        )
        self.client.post(reverse("partidas:iniciar", kwargs={"pk": partida.pk}))
        mano = ManoPoker.objects.get(partida=partida)
        return partida, mano, participacion_1, participacion_2
