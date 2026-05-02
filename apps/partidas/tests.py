from django.test import TestCase
from django.urls import reverse

from apps.partidas.evaluador import comparar_manos, evaluar_mejor_mano
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
        self.assertEqual(mano.incremento_minimo_subida, partida.ciega_grande)

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
        participacion_2.refresh_from_db()
        self.assertEqual(mano.estado, EstadoMano.FINALIZADA)
        self.assertEqual(mano.ganador, participacion_2)
        self.assertFalse(participacion_1.activa_en_mano)
        self.assertEqual(participacion_2.fichas, 1010)
        self.assertEqual(mano.descripcion_resultado, "Gana por retirada del resto de jugadores")
        self.assertEqual(mano.ganadores.count(), 1)
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

    def test_subir_actualiza_apuesta_bote_y_reabre_la_ronda(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa subida",
            maximo_jugadores=5,
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
        participacion_3 = ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.tercer_usuario,
            numero_asiento=3,
            estado=EstadoParticipacion.UNIDO,
        )
        self.client.post(reverse("partidas:iniciar", kwargs={"pk": partida.pk}))
        mano = ManoPoker.objects.get(partida=partida)

        self.client.logout()
        self.client.login(username="jugador3", password="ClaveSegura123!")
        response = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "subir", "objetivo_subida": "60"},
        )

        self.assertRedirects(response, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        mano.refresh_from_db()
        participacion_1.refresh_from_db()
        participacion_2.refresh_from_db()
        participacion_3.refresh_from_db()
        self.assertEqual(mano.turno_actual, participacion_1)
        self.assertEqual(mano.apuesta_actual_ronda, 60)
        self.assertEqual(mano.incremento_minimo_subida, 40)
        self.assertEqual(mano.bote_total, 90)
        self.assertEqual(participacion_3.apuesta_en_ronda, 60)
        self.assertEqual(participacion_3.fichas, 940)
        self.assertFalse(participacion_1.ha_actuado_en_ronda)
        self.assertFalse(participacion_2.ha_actuado_en_ronda)

    def test_no_se_permita_una_subida_por_debajo_del_minimo(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa subida invalida",
            maximo_jugadores=5,
            ciega_pequena=10,
            ciega_grande=20,
        )
        ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.usuario,
            numero_asiento=1,
            estado=EstadoParticipacion.UNIDO,
        )
        ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.segundo_usuario,
            numero_asiento=2,
            estado=EstadoParticipacion.UNIDO,
        )
        participacion_3 = ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.tercer_usuario,
            numero_asiento=3,
            estado=EstadoParticipacion.UNIDO,
        )
        self.client.post(reverse("partidas:iniciar", kwargs={"pk": partida.pk}))
        mano = ManoPoker.objects.get(partida=partida)

        self.client.logout()
        self.client.login(username="jugador3", password="ClaveSegura123!")
        response = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "subir", "objetivo_subida": "30"},
            follow=True,
        )

        mano.refresh_from_db()
        participacion_3.refresh_from_db()
        self.assertContains(response, "La subida minima actual es hasta 40 fichas.")
        self.assertEqual(mano.apuesta_actual_ronda, 20)
        self.assertEqual(mano.bote_total, 30)
        self.assertEqual(mano.turno_actual, participacion_3)
        self.assertEqual(participacion_3.apuesta_en_ronda, 0)
        self.assertEqual(participacion_3.fichas, 1000)

    def test_no_se_puede_iniciar_otra_mano_mientras_haya_una_activa(self):
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

        partida.refresh_from_db()
        mano.refresh_from_db()
        self.assertEqual(mano.estado, EstadoMano.FLOP)
        self.assertFalse(partida.puede_iniciarse())

    def test_showdown_asigna_ganador_y_reparte_bote_al_final_del_river(self):
        partida, mano, participacion_1, participacion_2 = self._crear_partida_iniciada()
        mano.estado = EstadoMano.RIVER
        mano.turno_actual = participacion_1
        mano.apuesta_actual_ronda = 0
        mano.bote_total = 100
        mano.cartas_comunitarias = "2P,5D,9T,JC,KP"
        mano.save(
            update_fields=[
                "estado",
                "turno_actual",
                "apuesta_actual_ronda",
                "bote_total",
                "cartas_comunitarias",
            ]
        )
        mano.cartas_privadas.filter(participacion=participacion_1).delete()
        mano.cartas_privadas.filter(participacion=participacion_2).delete()
        CartaPrivada.objects.create(mano=mano, participacion=participacion_1, orden=1, codigo="AP")
        CartaPrivada.objects.create(mano=mano, participacion=participacion_1, orden=2, codigo="AD")
        CartaPrivada.objects.create(mano=mano, participacion=participacion_2, orden=1, codigo="QP")
        CartaPrivada.objects.create(mano=mano, participacion=participacion_2, orden=2, codigo="QD")
        participacion_1.fichas = 900
        participacion_1.apuesta_en_ronda = 0
        participacion_1.ha_actuado_en_ronda = False
        participacion_1.save(update_fields=["fichas", "apuesta_en_ronda", "ha_actuado_en_ronda"])
        participacion_2.fichas = 900
        participacion_2.apuesta_en_ronda = 0
        participacion_2.ha_actuado_en_ronda = False
        participacion_2.save(update_fields=["fichas", "apuesta_en_ronda", "ha_actuado_en_ronda"])

        response_1 = self.client.post(
            reverse("partidas:accion", kwargs={"pk": partida.pk}),
            data={"tipo_accion": "pasar"},
        )
        self.assertRedirects(response_1, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
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
        self.assertEqual(mano.estado, EstadoMano.FINALIZADA)
        self.assertEqual(mano.ganador, participacion_1)
        self.assertEqual(mano.descripcion_resultado, "jugador1 gana con pareja")
        self.assertEqual(participacion_1.fichas, 1000)
        self.assertEqual(participacion_2.fichas, 900)
        self.assertEqual(list(mano.ganadores.values_list("usuario__username", flat=True)), ["jugador1"])

    def test_showdown_reparte_bote_empatado(self):
        partida, mano, participacion_1, participacion_2 = self._crear_partida_iniciada()
        mano.estado = EstadoMano.RIVER
        mano.turno_actual = participacion_1
        mano.apuesta_actual_ronda = 0
        mano.bote_total = 101
        mano.cartas_comunitarias = "AP,KD,QT,JC,10P"
        mano.save(
            update_fields=[
                "estado",
                "turno_actual",
                "apuesta_actual_ronda",
                "bote_total",
                "cartas_comunitarias",
            ]
        )
        mano.cartas_privadas.all().delete()
        CartaPrivada.objects.create(mano=mano, participacion=participacion_1, orden=1, codigo="2C")
        CartaPrivada.objects.create(mano=mano, participacion=participacion_1, orden=2, codigo="3C")
        CartaPrivada.objects.create(mano=mano, participacion=participacion_2, orden=1, codigo="4D")
        CartaPrivada.objects.create(mano=mano, participacion=participacion_2, orden=2, codigo="5D")
        participacion_1.fichas = 900
        participacion_1.apuesta_en_ronda = 0
        participacion_1.ha_actuado_en_ronda = False
        participacion_1.save(update_fields=["fichas", "apuesta_en_ronda", "ha_actuado_en_ronda"])
        participacion_2.fichas = 900
        participacion_2.apuesta_en_ronda = 0
        participacion_2.ha_actuado_en_ronda = False
        participacion_2.save(update_fields=["fichas", "apuesta_en_ronda", "ha_actuado_en_ronda"])

        self.client.post(reverse("partidas:accion", kwargs={"pk": partida.pk}), data={"tipo_accion": "pasar"})
        self.client.logout()
        self.client.login(username="jugador2", password="ClaveSegura123!")
        self.client.post(reverse("partidas:accion", kwargs={"pk": partida.pk}), data={"tipo_accion": "pasar"})

        mano.refresh_from_db()
        participacion_1.refresh_from_db()
        participacion_2.refresh_from_db()
        self.assertEqual(mano.estado, EstadoMano.FINALIZADA)
        self.assertIsNone(mano.ganador)
        self.assertEqual(mano.ganadores.count(), 2)
        self.assertEqual(participacion_1.fichas, 951)
        self.assertEqual(participacion_2.fichas, 950)
        self.assertIn("Empate entre", mano.descripcion_resultado)

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


class EvaluadorManosTests(TestCase):
    def test_detecta_poker_como_mejor_mano(self):
        resultado = evaluar_mejor_mano(["AP", "AD", "AC", "AT", "KP", "QD", "JC"])
        self.assertEqual(resultado["nombre"], "Poker")

    def test_detecta_escalera_de_color_como_superior_a_full(self):
        usuario_1 = object()
        usuario_2 = object()
        ganadores = comparar_manos(
            {
                usuario_1: ["9P", "8P", "7P", "6P", "5P", "2D", "AC"],
                usuario_2: ["KP", "KD", "KC", "2P", "2C", "3D", "4T"],
            }
        )
        self.assertEqual(len(ganadores), 1)
        self.assertIs(ganadores[0]["participacion"], usuario_1)
        self.assertEqual(ganadores[0]["nombre"], "Escalera de color")
