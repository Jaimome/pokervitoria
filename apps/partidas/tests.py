from django.test import TestCase
from django.urls import reverse

from apps.partidas.models import CartaPrivada, EstadoPartida, ManoPoker, ParticipacionPartida, PartidaPoker
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

    def test_se_puede_iniciar_una_partida_con_dos_jugadores_y_repartir_cartas(self):
        partida = PartidaPoker.objects.create(
            nombre="Mesa activa",
            maximo_jugadores=4,
            ciega_pequena=10,
            ciega_grande=20,
        )
        ParticipacionPartida.objects.create(partida=partida, usuario=self.usuario, numero_asiento=1)
        ParticipacionPartida.objects.create(
            partida=partida,
            usuario=self.segundo_usuario,
            numero_asiento=2,
        )

        response = self.client.post(reverse("partidas:iniciar", kwargs={"pk": partida.pk}))

        self.assertRedirects(response, reverse("partidas:detalle", kwargs={"pk": partida.pk}))
        partida.refresh_from_db()
        self.assertEqual(partida.estado, EstadoPartida.EN_CURSO)
        mano = ManoPoker.objects.get(partida=partida)
        self.assertEqual(mano.cartas_privadas.count(), 4)
        self.assertEqual(
            CartaPrivada.objects.filter(mano=mano, participacion__usuario=self.usuario).count(),
            2,
        )
