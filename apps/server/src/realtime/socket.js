const { Server } = require("socket.io");
const { addPlayer, listPlayers, removePlayer } = require("../state/roomsStore");

function setupSocket(httpServer) {
  const io = new Server(httpServer, {
    cors: { origin: "*" }, // luego lo restringimos
  });

  io.on("connection", (socket) => {
    console.log("socket connected:", socket.id);

    socket.on("room:join", (payload) => {
      const { roomId, playerName } = payload ?? {};

      if (!roomId || typeof roomId !== "string") {
        return socket.emit("error", {
          error: "Bad Request",
          details: "roomId required",
        });
      }
      if (
        !playerName ||
        typeof playerName !== "string" ||
        playerName.trim().length < 2
      ) {
        return socket.emit("error", {
          error: "Bad Request",
          details: "playerName required (min 2 chars)",
        });
      }

      const result = addPlayer(roomId, playerName);

      if (result.error === "ROOM_NOT_FOUND") {
        return socket.emit("error", { error: "Room not found" });
      }
      if (result.error === "NAME_TAKEN") {
        return socket.emit("error", { error: "Name taken" });
      }

      // Unimos el socket a la room de Socket.io
      socket.join(roomId);

      // Guardamos en el socket “quién es” para poder limpiarlo en disconnect
      socket.data.roomId = roomId;
      socket.data.playerId = result.player.id;

      // Confirmación al que se une
      socket.emit("room:joined", { roomId, player: result.player });

      // Broadcast a todos en la sala con la lista de jugadores actualizada
      const playersResult = listPlayers(roomId);
      io.to(roomId).emit("room:players", {
        roomId,
        players: playersResult.players,
      });
    });

    socket.on("room:leave", () => {
      const { roomId, playerId } = socket.data ?? {};
      if (!roomId || !playerId) return;

      // 1) saca del store
      removePlayer(roomId, playerId);

      // 2) saca el socket de la room de socket.io
      socket.leave(roomId);

      // 3) limpia metadata
      delete socket.data.roomId;
      delete socket.data.playerId;

      // 4) broadcast lista actualizada
      const playersResult = listPlayers(roomId);
      if (!playersResult.error) {
        io.to(roomId).emit("room:players", {
          roomId,
          players: playersResult.players,
        });
      }

      socket.emit("room:left", { roomId });
    });

    socket.on("disconnect", () => {
      const { roomId, playerId } = socket.data ?? {};
      if (!roomId || !playerId) return;

      removePlayer(roomId, playerId);

      const playersResult = listPlayers(roomId);
      if (!playersResult.error) {
        io.to(roomId).emit("room:players", {
          roomId,
          players: playersResult.players,
        });
      }

      console.log("socket disconnected:", socket.id);
    });
  });

  return io;
}

module.exports = { setupSocket };
