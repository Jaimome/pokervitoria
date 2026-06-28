from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ConsumidorPartida(AsyncJsonWebsocketConsumer):
    """Canal websocket para refrescar el detalle de una partida en vivo."""

    async def connect(self):
        partida_id = str(self.scope["url_route"]["kwargs"]["partida_id"])
        self.nombre_grupo = f"partida_{partida_id}"

        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.nombre_grupo, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "tipo": "conexion_establecida",
                "mensaje": "Canal en tiempo real conectado.",
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.nombre_grupo, self.channel_name)

    async def refrescar_partida(self, event):
        await self.send_json(
            {
                "tipo": "refrescar_partida",
                "motivo": event["motivo"],
            }
        )
