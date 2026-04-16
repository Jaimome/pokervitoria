from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notificar_cambio_partida(partida_id, motivo: str) -> None:
    """Emite un evento websocket para que la mesa se refresque en vivo."""

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"partida_{partida_id}",
        {
            "type": "refrescar_partida",
            "motivo": motivo,
        },
    )
