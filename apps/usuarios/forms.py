from django import forms
from django.contrib.auth.forms import UserCreationForm

from apps.usuarios.models import Usuario


class FormularioRegistroUsuario(UserCreationForm):
    """Formulario minimo de registro para la primera version del proyecto."""

    email = forms.EmailField(label="Correo electronico")

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "nombre_mostrado", "email")
        labels = {
            "username": "Nombre de usuario",
            "nombre_mostrado": "Nombre mostrado",
        }
