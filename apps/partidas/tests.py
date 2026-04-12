from django.test import TestCase
from django.urls import reverse

from apps.partidas.models import ParticipacionPartida, PartidaPoker
from apps.usuarios.models import Usuario


class FlujoPartidasTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="jugador1",
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
