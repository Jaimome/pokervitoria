# Devlog — 2026-01-28 — Lobby realtime (Rooms + Players + Socket.io + UI React)

## Contexto

Partíamos de un backend Express funcionando con:

- `GET /` → `{ message: "API ok" }`
- `GET /health` → `{ status, uptimeSeconds, timestamp }`
- 404 en JSON y errorHandler en JSON
- `.env` + `dotenv` (PORT + NODE_ENV)
- Rutas REST para rooms/players ya creadas previamente

Objetivo del día:

1. Separar el estado (rooms/players) de las rutas REST.
2. Añadir endpoints REST de listado y borrado.
3. Montar Socket.io mínimo con “join/leave” y broadcast de players.
4. Conectar el frontend React (Vite) al Socket.io para ver el lobby en el navegador.

---

## Paso 10 — Store en memoria (separar estado de las rutas)

### Problema

La variable `rooms` (Map) estaba dentro del router `routes/rooms.js`.
Eso dificulta reutilizar la lógica desde Socket.io y complica el crecimiento.

### Solución

Crear un módulo “store” que guarda estado y ofrece funciones.

**Archivo creado:** `apps/server/src/state/roomsStore.js`

Contiene:

- `createRoom(name)`
- `getRoom(id)`
- `addPlayer(roomId, playerName)`
- `listPlayers(roomId)`

Cambios:

- `apps/server/src/routes/rooms.js` dejó de tener `const rooms = new Map()`
- Ahora importa funciones del store: `require("../state/roomsStore")`

### Incidencia encontrada

`POST /rooms` devolvía `404 Not Found`.

Causa: `roomsRouter` no estaba montado (o estaba montado después del `notFound`).

Solución: asegurar en `apps/server/src/app.js`:

- `app.use("/", roomsRouter);` antes de:
- `app.use(notFound);`

---

## Paso 11 — REST extra: listar y borrar rooms

Objetivo: poder probar más rápido sin reiniciar servidor.

### Cambios en store

En `roomsStore.js` se añadieron:

- `listRooms()` → devuelve lista resumida con `{ id, name, playersCount, createdAt }`
- `deleteRoom(id)` → borra del Map y devuelve true/false

### Cambios en rutas

En `apps/server/src/routes/rooms.js` se añadieron:

- `GET /rooms` → `{ rooms: [...] }`
- `DELETE /rooms/:id` → `204 No Content` si borra, `404` si no existe

### Verificación

- Crear room por REST, listar, borrar, listar de nuevo → OK.

---

## Paso 12 — Socket.io mínimo (sin frontend todavía)

Objetivo: tener lobby realtime por WebSocket usando el MISMO store.

### Dependencias

En `apps/server`:

- `npm i socket.io`
- `npm i -D socket.io-client` (solo para test)

### Archivos creados / modificados

**Creado:** `apps/server/src/realtime/socket.js`

- `setupSocket(httpServer)` crea `io` y define listeners.

Eventos:

- `room:join` (payload: `{ roomId, playerName }`)
  - valida input
  - `addPlayer(roomId, playerName)`
  - `socket.join(roomId)` (room de socket.io)
  - guarda `socket.data.roomId` y `socket.data.playerId`
  - emite al propio socket: `room:joined`
  - emite a toda la sala: `room:players` con lista actualizada

- `disconnect`
  - si el socket estaba en una room, borra el jugador y re-emite `room:players`

**Modificado:** `apps/server/src/state/roomsStore.js`

- Añadido `removePlayer(roomId, playerId)` para poder limpiar jugadores al desconectar.

**Modificado:** `apps/server/src/index.js`
Antes: `app.listen(PORT)`
Ahora:

- crear `httpServer = http.createServer(app)`
- llamar `setupSocket(httpServer)`
- `httpServer.listen(PORT)`

### Script de prueba (sin client web)

**Creado:** `apps/server/scripts/socket-test.js`

- conecta con `socket.io-client`
- emite `room:join`
- escucha `room:joined` y `room:players`

### Verificación

Con dos terminales:

- “Jaime” se une
- “Samuel” se une
- ambos reciben `room:players` actualizado → OK.

---

## Paso 12.5 / 12.6 — Evento explícito `room:leave`

Objetivo: poder salir de la sala sin cerrar pestaña (necesario para UI real).

### Cambios

En `apps/server/src/realtime/socket.js`:

- Nuevo evento: `room:leave`
  - `removePlayer(...)`
  - `socket.leave(roomId)`
  - limpia `socket.data.*`
  - emite:
    - al propio socket: `room:left`
    - a la sala: `room:players` actualizado

En el script `socket-test.js`:

- se añadió listener `room:left`
- se añadió `setTimeout(... socket.emit("room:leave") ...)` para probar.

### Verificación

- al cabo de 5s “Jaime” sale automáticamente
- “Samuel” ve que desaparece en `room:players` → OK.

---

## Paso 13 — Frontend con Vite + React

Objetivo: UI mínima para lobby realtime.

### Setup

En `apps/client`:

- `npm create vite@latest . -- --template react`
- `npm install`
- `npm i socket.io-client`
- `npm run dev`

Nota: si el puerto 5173 está ocupado, Vite usa otro (p.ej. 5174).

---

## Paso 14 — UI mínima Join/Players/Leave

### Config

**Creado:** `apps/client/.env`

- `VITE_SERVER_URL=http://localhost:3001`

### UI

**Modificado:** `apps/client/src/App.jsx`
UI mínima con:

- inputs: `roomId`, `playerName`
- botón Join (emite `room:join`)
- botón Leave (emite `room:leave`)
- estado “connected/disconnected”
- lista de players en vivo con `room:players`
- manejo de errores mostrando mensaje

Notas:

- el socket se crea con `autoConnect: false`
- en join se hace `socket.connect()` si no estaba conectado
- cleanup: `removeAllListeners()` y `disconnect()` en un `useEffect` cleanup.

### Verificación final

- abrir 2 pestañas
- mismo `roomId`, distintos nombres
- la lista se sincroniza en tiempo real
- Leave elimina jugador y actualiza lista → OK.

---

## Resultado del día

✅ Backend REST + store en memoria bien separado  
✅ Lobby realtime por Socket.io (join/leave + broadcast de players)  
✅ UI React mínima que muestra players sincronizados en varias pestañas

Esto ya es un “vertical slice” funcional: **sala + jugadores online en tiempo real**.

---

## Próximos pasos propuestos

1. Deploy en Render (backend y frontend), sin DB todavía.
2. Añadir “mini juego” server-authoritative encima del lobby (turnos/acción simple).
3. Migrar backend a TypeScript cuando esté estable online.
