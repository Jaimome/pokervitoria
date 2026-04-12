from django.urls import path

from apps.partidas.views import (
    VistaAccionPartida,
    VistaAbandonarPartida,
    VistaCrearPartida,
    VistaDetallePartida,
    VistaIniciarPartida,
    VistaListaPartidas,
    VistaUnirsePartida,
)


app_name = "partidas"

urlpatterns = [
    path("", VistaListaPartidas.as_view(), name="lista"),
    path("crear/", VistaCrearPartida.as_view(), name="crear"),
    path("<uuid:pk>/", VistaDetallePartida.as_view(), name="detalle"),
    path("<uuid:pk>/unirse/", VistaUnirsePartida.as_view(), name="unirse"),
    path("<uuid:pk>/iniciar/", VistaIniciarPartida.as_view(), name="iniciar"),
    path("<uuid:pk>/accion/", VistaAccionPartida.as_view(), name="accion"),
    path("<uuid:pk>/abandonar/", VistaAbandonarPartida.as_view(), name="abandonar"),
]
