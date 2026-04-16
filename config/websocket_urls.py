from django.urls import path

from apps.partidas.consumers import ConsumidorPartida


websocket_urlpatterns = [
    path("ws/partidas/<uuid:partida_id>/", ConsumidorPartida.as_asgi(), name="ws_partida"),
]
