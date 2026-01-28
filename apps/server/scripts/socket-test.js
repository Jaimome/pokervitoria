const { io } = require("socket.io-client");

const roomId = process.argv[2];
const playerName = process.argv[3] || "Jaime";

if (!roomId) {
  console.log("Usage: node scripts/socket-test.js <roomId> <playerName>");
  process.exit(1);
}

const socket = io("http://localhost:3001");

socket.on("connect", () => {
  console.log("connected", socket.id);
  socket.emit("room:join", { roomId, playerName });
});

socket.on("room:joined", (data) => console.log("room:joined", data));
socket.on("room:players", (data) => console.log("room:players", data));
socket.on("error", (e) => console.log("error", e));
socket.on("room:left", (data) => console.log("room:left", data));

setTimeout(() => {
  socket.emit("room:leave");
}, 5000);
