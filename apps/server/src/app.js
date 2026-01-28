const express = require("express");

const rootRouter = require("./routes/root");
const healthRouter = require("./routes/health");
const roomsRouter = require("./routes/rooms");
const debugRouter = require("./routes/debug");

const notFound = require("./middleware/notFound");
const errorHandler = require("./middleware/errorHandler");

const app = express();

// Para poder leer JSON en POST/PUT
app.use(express.json());

// Rutas
app.use("/", rootRouter);
app.use("/", healthRouter);
app.use("/", roomsRouter);

// Debug solo en development
if (process.env.NODE_ENV === "development") {
  app.use("/", debugRouter);
}

// 404 (si ninguna ruta anterior coincide)
app.use(notFound);

// Errores
app.use(errorHandler);

module.exports = app;
