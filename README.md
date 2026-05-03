# Pokervitoria

Pokervitoria es un `TFG` de Ingenieria Informatica centrado en el desarrollo de un poker online de `Texas Hold'em` que, ademas de ser jugable, esta pensado como caso de estudio docente.

La idea del proyecto es construir una base:

- funcional para jugar desde navegador
- mantenible y clara para evolucionarla con orden
- lo bastante documentada como para poder explicarla, analizarla y mejorarla

La tecnologia principal es:

- `Python`
- `Django`
- `Channels`
- `Daphne`
- `SQLite` en local
- `PostgreSQL` como base de datos objetivo para despliegue

## Que puede hacer ya la version actual

La version actual ya permite:

- abrir una aplicacion web funcional en navegador con interfaz vertical y minimalista
- mostrar una portada distinta para usuarios autenticados y no autenticados
- registrar usuarios
- iniciar sesion
- cerrar sesion
- borrar la cuenta desde perfil
- crear cuentas nuevas con un saldo inicial de `2.000` fichas
- mostrar el saldo total del jugador en la pantalla principal, en perfil y en ranking
- ver un ranking completo con todos los jugadores ordenados por saldo total
- consultar una pantalla de reglas del poker y de uso basico de la interfaz
- crear partidas privadas mediante un codigo unico editable
- copiar el codigo de una partida privada al portapapeles
- entrar en una partida privada usando un codigo existente
- buscar partida publica mediante una cola simple de emparejamiento
- cancelar la busqueda publica con confirmacion
- mostrar el numero de jugadores conectados a partir de sesiones autenticadas activas
- unirse a una partida descontando del saldo total un maximo de `200` fichas
- hacer que las fichas dentro de la partida y el saldo total del usuario queden separados
- devolver al saldo total las fichas restantes de la partida cuando el usuario sale de la mesa
- mantener el dinero dentro del sistema sin crearlo ni destruirlo durante las manos
- iniciar una mano con al menos dos jugadores
- repartir cartas privadas a cada jugador
- publicar automaticamente ciega pequena y ciega grande
- permitir `pasar`, `pagar`, `subir` y `retirarse`
- validar subidas minimas y cantidades a igualar
- avanzar automaticamente entre `preflop`, `flop`, `turn` y `river`
- revelar las cartas comunitarias segun la fase
- resolver el `showdown` al final de `river`
- evaluar combinaciones reales de `Texas Hold'em`
- repartir el bote al ganador o a varios ganadores en caso de empate
- mostrar el resultado final de la mano
- refrescar en tiempo real el detalle de la partida mediante `WebSockets`
- mostrar un contador de turno de `30` segundos para el jugador activo
- retirar automaticamente al jugador si deja pasar el tiempo
- ocultar por defecto las cartas privadas del jugador y mostrarlas solo al pasar el cursor
- mostrar una puntuacion orientativa de la mano en escala `01/10` a `10/10` cuando se revela la zona privada

## Como se prueba la version actual

Flujo basico recomendado:

1. abrir `http://127.0.0.1:8000/`
2. registrar varias cuentas o usar cuentas de prueba locales
3. comprobar que cada cuenta empieza con `2.000` fichas
4. probar `Buscar partida` con dos usuarios distintos
5. probar `Partida privada` creando una sala por codigo y entrando con otro usuario
6. iniciar una mano y jugar hasta `showdown`
7. comprobar que el saldo total cambia al entrar y salir de las partidas
8. comprobar que el detalle de la mesa se refresca en tiempo real en varias ventanas
9. comprobar que el hover sobre las cartas privadas revela las cartas y la puntuacion de mano

## Tiempo real

La mesa usa `WebSockets` para que varias ventanas de navegador vean cambios automaticamente.

Ahora mismo el detalle de partida se actualiza cuando:

- un jugador entra en la mesa
- un jugador sale de la mesa
- se inicia una mano
- un jugador actua

La vista muestra tambien un estado visible de conexion:

- `Tiempo real: conectando...`
- `Tiempo real: conectado`
- `Tiempo real: desconectado`
- `Tiempo real: error de conexion`

## Estado actual del alcance

El proyecto ya cubre una parte importante del flujo jugable de `Nivel 1` y deja muy adelantada la base de `Nivel 2`.

Lo mas importante que ya existe es:

- autenticacion completa de usuario
- economia basica con saldo total y fichas en mesa
- partidas publicas y privadas
- tiempo real basico
- una mano de `Texas Hold'em` jugable hasta `showdown`

Lo siguiente previsto es:

- encadenar varias manos seguidas dentro de una misma partida
- rotar posiciones y ciegas entre manos
- consolidar historial, ranking persistente y trazabilidad
