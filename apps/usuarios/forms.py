from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from apps.usuarios.models import Usuario


class FormularioRegistroUsuario(UserCreationForm):
    """Formulario minimo de registro para la primera version del proyecto."""

    email = forms.EmailField(label="Correo electronico")

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "email")
        labels = {
            "username": "Usuario",
        }


class FormularioInicioSesion(AuthenticationForm):
    """Formulario de inicio de sesion con terminologia unificada."""

    username = forms.CharField(label="Usuario")
