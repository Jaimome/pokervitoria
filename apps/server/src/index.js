require("dotenv").config();

const http = require("http");
const app = require("./app");
const { setupSocket } = require("./realtime/socket");

const PORT = process.env.PORT || 3001;

const httpServer = http.createServer(app);

// Socket.io vive “encima” del mismo server HTTP
setupSocket(httpServer);

httpServer.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
