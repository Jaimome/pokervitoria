from django import forms

from apps.partidas.models import PartidaPoker


class FormularioCrearPartida(forms.ModelForm):
    """Formulario mínimo para crear una nueva mesa de juego."""

    class Meta:
        model = PartidaPoker
        fields = ("nombre", "maximo_jugadores", "ciega_pequena", "ciega_grande")
        labels = {
            "nombre": "Nombre de la partida",
            "maximo_jugadores": "Máximo de jugadores",
            "ciega_pequena": "Ciega pequeña",
            "ciega_grande": "Ciega grande",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "entrada-texto"})


class FormularioPartidaPrivada(forms.Form):
    codigo_creacion = forms.CharField(
        label="Código de la partida",
        max_length=16,
        required=False,
    )
    codigo_entrada = forms.CharField(
        label="Código para entrar",
        max_length=16,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo_creacion"].widget.attrs.update(
            {
                "class": "entrada-texto",
                "placeholder": "Código de la partida",
                "autocomplete": "off",
            }
        )
        self.fields["codigo_entrada"].widget.attrs.update(
            {
                "class": "entrada-texto",
                "placeholder": "Introduce un código existente",
                "autocomplete": "off",
            }
        )
