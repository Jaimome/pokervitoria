// Express es el framework que usamos para construir la API HTTP (rutas tipo GET/POST)
// Piensa en Express como “el router” y el “motor” que gestiona requests y responses.
const express = require("express");

// Routers (grupos de rutas HTTP) separados por responsabilidad.
// Cada router define endpoints concretos y luego aquí los “enchufamos” a la app.
const rootRouter = require("./routes/root");
const healthRouter = require("./routes/health");
const roomsRouter = require("./routes/rooms");
const debugRouter = require("./routes/debug");

// Middlewares globales (se ejecutan en orden).
// - notFound: respuesta 404 JSON cuando no existe ninguna ruta.
// - errorHandler: captura errores y devuelve un JSON de error coherente.
const notFound = require("./middleware/notFound");
const errorHandler = require("./middleware/errorHandler");

// Creamos la instancia principal de Express.
// "app" es el objeto donde montamos middlewares y rutas.
const app = express();

// Middleware built-in de Express para parsear JSON en el body.
// Sin esto, req.body sería undefined en POST/PUT con JSON.
app.use(express.json());

// Montamos routers.
// El primer argumento "/" es el "prefijo": significa que las rutas del router
// se registran tal cual (por ejemplo, rootRouter define GET "/" y queda en GET "/").
app.use("/", rootRouter);
app.use("/", healthRouter);
app.use("/", roomsRouter);

// Router de debug SOLO en desarrollo.
// Motivo: endpoints de debug pueden ser peligrosos o innecesarios en producción.
if (process.env.NODE_ENV === "development") {
  app.use("/", debugRouter);
}

// Middleware 404: debe ir DESPUÉS de todas las rutas.
// Si ninguna ruta anterior ha respondido, llegamos aquí y devolvemos 404.
app.use(notFound);

// Middleware de errores: siempre al final.
// Express lo ejecuta cuando ocurre un error (throw / next(err)) en rutas o middlewares.
app.use(errorHandler);

// Exportamos la app para que index.js la monte en el servidor HTTP.
module.exports = app;
