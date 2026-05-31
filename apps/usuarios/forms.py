from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from apps.usuarios.models import Usuario


class FormularioRegistroUsuario(UserCreationForm):
    """Formulario minimo de registro para la primera version del proyecto."""

    username = forms.CharField(label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Contraseña (confirmación)", widget=forms.PasswordInput)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "entrada-texto", "autocomplete": "username"})
        self.fields["email"].widget.attrs.update({"class": "entrada-texto", "autocomplete": "email"})
        self.fields["password1"].widget.attrs.update({"class": "entrada-texto", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"class": "entrada-texto", "autocomplete": "new-password"})


class FormularioInicioSesion(AuthenticationForm):
    """Formulario de inicio de sesión con terminología unificada."""

    username = forms.CharField(label="Nombre de usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "entrada-texto", "autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"class": "entrada-texto", "autocomplete": "current-password"})
