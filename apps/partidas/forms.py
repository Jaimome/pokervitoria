from django import forms

from apps.partidas.models import PartidaPoker


class FormularioCrearPartida(forms.ModelForm):
    """Formulario minimo para crear una nueva mesa de juego."""

    class Meta:
        model = PartidaPoker
        fields = ("nombre", "maximo_jugadores", "ciega_pequena", "ciega_grande")
        labels = {
            "nombre": "Nombre de la partida",
            "maximo_jugadores": "Maximo de jugadores",
            "ciega_pequena": "Ciega pequena",
            "ciega_grande": "Ciega grande",
        }
