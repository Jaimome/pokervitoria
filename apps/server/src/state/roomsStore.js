const crypto = require("crypto");

const rooms = new Map();

function createRoom(name) {
  const id = crypto.randomUUID();
  const room = {
    id,
    name: name.trim(),
    players: [],
    createdAt: new Date().toISOString(),
  };
  rooms.set(id, room);
  return room;
}

function getRoom(id) {
  return rooms.get(id) || null;
}

function addPlayer(roomId, playerName) {
  const room = getRoom(roomId);
  if (!room) return { error: "ROOM_NOT_FOUND" };

  const cleanName = playerName.trim();

  const nameTaken = room.players.some(
    (p) => p.name.toLowerCase() === cleanName.toLowerCase(),
  );
  if (nameTaken) return { error: "NAME_TAKEN" };

  const player = {
    id: crypto.randomUUID(),
    name: cleanName,
    joinedAt: new Date().toISOString(),
  };

  room.players.push(player);
  return { room, player };
}

function listPlayers(roomId) {
  const room = getRoom(roomId);
  if (!room) return { error: "ROOM_NOT_FOUND" };
  return { room, players: room.players };
}

function listRooms() {
  return Array.from(rooms.values()).map((r) => ({
    id: r.id,
    name: r.name,
    playersCount: r.players.length,
    createdAt: r.createdAt,
  }));
}

function deleteRoom(id) {
  return rooms.delete(id); // true si existía, false si no
}

function removePlayer(roomId, playerId) {
  const room = getRoom(roomId);
  if (!room) return false;

  const before = room.players.length;
  room.players = room.players.filter((p) => p.id !== playerId);
  return room.players.length !== before;
}

module.exports = {
  createRoom,
  getRoom,
  addPlayer,
  listPlayers,
  listRooms,
  deleteRoom,
  removePlayer,
};
