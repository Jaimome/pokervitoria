from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario


class AutenticacionTests(TestCase):
    def test_el_registro_crea_un_usuario_y_abre_sesion(self):
        response = self.client.post(
            reverse("usuarios:registro"),
            data={
                "username": "ana",
                "email": "ana@example.com",
                "password1": "ClaveSegura123!",
                "password2": "ClaveSegura123!",
            },
        )

        self.assertRedirects(response, reverse("nucleo:inicio"))
        self.assertTrue(Usuario.objects.filter(username="ana").exists())
        usuario = Usuario.objects.get(username="ana")
        self.assertEqual(usuario.saldo_total, 2000)
        self.assertEqual(self.client.get(reverse("usuarios:perfil")).status_code, 200)

    def test_el_perfil_requiere_autenticacion(self):
        response = self.client.get(reverse("usuarios:perfil"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("usuarios:iniciar_sesion"), response.url)

    def test_borrar_cuenta_elimina_al_usuario_autenticado(self):
        usuario = Usuario.objects.create_user(
            username="borrar",
            password="ClaveSegura123!",
            email="borrar@example.com",
        )
        self.client.login(username="borrar", password="ClaveSegura123!")

        response = self.client.post(reverse("usuarios:borrar_cuenta"))

        self.assertRedirects(response, reverse("nucleo:inicio"))
        self.assertFalse(Usuario.objects.filter(pk=usuario.pk).exists())
