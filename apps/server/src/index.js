// Carga variables de entorno desde el archivo .env (por defecto: apps/server/.env)
// Resultado: process.env.PORT, process.env.NODE_ENV, etc. quedan disponibles en el código.
require("dotenv").config();

// Módulo nativo de Node para crear un servidor HTTP “real”
const http = require("http");

// Importamos la app de Express (rutas + middlewares).
// Ojo: Express por sí solo no "escucha" en un puerto hasta que lo montas en un server.
const app = require("./app");

// Importamos la función que inicializa Socket.io y registra sus eventos.
// socket.io necesita un servidor HTTP para engancharse encima.
const { setupSocket } = require("./realtime/socket");

// Elegimos el puerto:
// - En hosting (Render), PORT viene en variables de entorno.
// - En local, usamos 3001 como fallback.
const PORT = process.env.PORT || 3001;

// Creamos el servidor HTTP usando la app de Express como “handler”.
// Esto significa: cada petición HTTP que llegue, Express la gestiona (GET /, POST /rooms, etc.).
const httpServer = http.createServer(app);

// Montamos Socket.io “encima” del mismo servidor HTTP.
// Ventaja: HTTP (REST) y WebSocket (tiempo real) comparten el mismo host y puerto.
setupSocket(httpServer);

// Ponemos el servidor a escuchar en el puerto elegido.
// A partir de aquí, el backend está “vivo” y aceptando conexiones.
httpServer.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
