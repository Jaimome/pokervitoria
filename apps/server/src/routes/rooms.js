const express = require("express");

const {
  createRoom,
  getRoom,
  addPlayer,
  listPlayers,
  listRooms,
  deleteRoom,
} = require("../state/roomsStore");

const router = express.Router();

router.get("/rooms", (_req, res) => {
  return res.status(200).json({ rooms: listRooms() });
});

// Crear sala
router.post("/rooms", (req, res) => {
  const { name } = req.body ?? {};

  if (!name || typeof name !== "string" || name.trim().length < 2) {
    return res.status(400).json({
      error: "Bad Request",
      details: "Field 'name' is required (string, min 2 chars).",
    });
  }

  const room = createRoom(name);
  return res.status(201).json(room);
});

// Obtener sala
router.get("/rooms/:id", (req, res) => {
  const room = getRoom(req.params.id);

  if (!room) {
    return res.status(404).json({ error: "Room not found" });
  }

  return res.status(200).json(room);
});

// Unirse a sala
router.post("/rooms/:id/join", (req, res) => {
  const { playerName } = req.body ?? {};

  if (
    !playerName ||
    typeof playerName !== "string" ||
    playerName.trim().length < 2
  ) {
    return res.status(400).json({
      error: "Bad Request",
      details: "Field 'playerName' is required (string, min 2 chars).",
    });
  }

  const result = addPlayer(req.params.id, playerName);

  if (result.error === "ROOM_NOT_FOUND") {
    return res.status(404).json({ error: "Room not found" });
  }
  if (result.error === "NAME_TAKEN") {
    return res.status(409).json({
      error: "Conflict",
      details: "Player name already taken in this room.",
    });
  }

  return res.status(201).json({
    roomId: result.room.id,
    player: result.player,
  });
});

// Listar jugadores
router.get("/rooms/:id/players", (req, res) => {
  const result = listPlayers(req.params.id);

  if (result.error === "ROOM_NOT_FOUND") {
    return res.status(404).json({ error: "Room not found" });
  }

  return res.status(200).json({
    roomId: result.room.id,
    players: result.players,
  });
});

router.delete("/rooms/:id", (req, res) => {
  const ok = deleteRoom(req.params.id);

  if (!ok) {
    return res.status(404).json({ error: "Room not found" });
  }

  return res.status(204).send();
});

module.exports = router;
