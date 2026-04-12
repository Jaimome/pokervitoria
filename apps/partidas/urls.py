from django.urls import path

from apps.partidas.views import (
    VistaCrearPartida,
    VistaDetallePartida,
    VistaListaPartidas,
    VistaUnirsePartida,
)


app_name = "partidas"

urlpatterns = [
    path("", VistaListaPartidas.as_view(), name="lista"),
    path("crear/", VistaCrearPartida.as_view(), name="crear"),
    path("<uuid:pk>/", VistaDetallePartida.as_view(), name="detalle"),
    path("<uuid:pk>/unirse/", VistaUnirsePartida.as_view(), name="unirse"),
]
