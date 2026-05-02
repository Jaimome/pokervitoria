# Pokervitoria

Pokervitoria es mi `TFG` de Ingenieria Informatica y consiste en el desarrollo de un videojuego online de `Texas Hold'em`.

El proyecto tiene un doble objetivo:

- construir un poker online funcional donde varios jugadores puedan registrarse, entrar, jugar partidas y consultar resultados
- usar ese sistema como caso de estudio para distintas asignaturas de la carrera

Eso significa que Pokervitoria no solo debe funcionar, sino que tambien debe ser:

- mantenible
- entendible
- bien documentado
- defendible a nivel academico

La tecnologia principal del proyecto sera:

- `Python`
- `Django`
- `PostgreSQL`

El alcance del trabajo parte de un prototipo jugable completo y evoluciona hacia una plataforma docente mas solida, con mejor arquitectura, trazabilidad, estadisticas y despliegue reproducible.

## Version actual

La version actual del proyecto ya permite:

- arrancar una aplicacion web funcional en `Django`
- registrar usuarios
- iniciar y cerrar sesion
- mostrar el nombre mostrado del usuario autenticado en la navegacion
- consultar un perfil autenticado
- persistir usuarios, partidas, participaciones y manos en base de datos local
- crear partidas desde navegador
- ver el listado de partidas disponibles
- unirse a una partida existente
- salir de una partida y volver a entrar despues
- ver el detalle de una mesa con sus participantes
- iniciar una mano con al menos dos jugadores
- repartir cartas privadas a cada jugador
- publicar automaticamente ciega pequena y ciega grande
- mostrar el turno actual
- permitir acciones basicas de `pasar`, `igualar` y `retirarse`
- permitir la accion de `subir` con una cantidad objetivo valida
- avanzar automaticamente entre `preflop`, `flop`, `turn` y `river`
- mostrar cartas comunitarias segun avanza la mano
- resolver el `showdown` al final de la mano si nadie se retira
- evaluar combinaciones reales de `Texas Hold'em`
- repartir el bote al ganador o repartirlo entre varios jugadores si hay empate
- mostrar el resultado final de la mano y la combinacion ganadora
- cerrar automaticamente la mano si solo queda un jugador activo
- refrescar en tiempo real el detalle de una partida cuando cambia su estado

## Tiempo real

La mesa de partida cuenta ya con una primera base de tiempo real mediante `WebSockets`.

En la version actual, cuando alguien:

- se une a una partida
- sale de una partida
- inicia una mano
- realiza una accion

los navegadores que esten viendo esa misma mesa se actualizan automaticamente.

En la mesa tambien se muestra ya:

- cuanto falta por igualar en tu turno
- cual es la subida minima legal en ese momento
- un campo para indicar hasta que cantidad quieres subir
- quien ha ganado la mano al resolverse el showdown
- si ha habido empate y como se ha repartido el bote

Para facilitar las pruebas, la vista de detalle de partida muestra tambien un estado visible de conexion:

- `Tiempo real: conectando...`
- `Tiempo real: conectado`
- `Tiempo real: desconectado`
- `Tiempo real: error de conexion`

## Dependencias actuales

La version actual utiliza estas dependencias principales:

- `Django`
- `Channels`
- `Daphne`

El siguiente bloque de trabajo sera encadenar varias manos seguidas dentro de una misma partida, rotando posiciones y ciegas.
