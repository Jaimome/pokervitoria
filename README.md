# pokerVitoria

`pokerVitoria` es un Proyecto de Fin de Grado de Ingenieria Informatica centrado en el desarrollo de una aplicacion web para jugar partidas online de `Texas Hold'em`.

El objetivo del proyecto es construir una base funcional, mantenible y documentada que permita explicar con claridad el funcionamiento de un juego multijugador en navegador: autenticacion, partidas, economia interna, tiempo real, reglas de poker y despliegue reproducible.

## Stack tecnico

- `Python`
- `Django`
- `Django Channels`
- `Daphne`
- `SQLite` para desarrollo local
- `PostgreSQL` para despliegue
- `WhiteNoise` para servir archivos estaticos en produccion

## Funcionalidades actuales

La version actual permite:

- registrar usuarios, iniciar sesion, cerrar sesion y borrar cuenta
- crear cuentas con un saldo inicial de `2.000` fichas
- mostrar el saldo total en inicio, perfil y ranking
- consultar un ranking completo de jugadores ordenado por saldo
- acceder a una pantalla de reglas y explicacion basica de la interfaz
- crear partidas privadas mediante codigo unico editable
- copiar el codigo de una partida privada
- entrar en una partida privada usando un codigo existente
- buscar partida publica mediante una cola simple de emparejamiento
- cancelar la busqueda publica con confirmacion
- separar saldo total y fichas dentro de una partida
- entrar a una partida con un maximo de `200` fichas
- devolver al saldo total las fichas no comprometidas al salir de una mesa
- iniciar una mano con al menos dos jugadores
- publicar automaticamente ciega pequena y ciega grande
- jugar acciones de `pasar`, `pagar`, `subir` y `retirarse`
- validar turnos, subidas minimas y cantidades pendientes
- avanzar por las fases `preflop`, `flop`, `turn` y `river`
- revelar cartas comunitarias segun la fase de la mano
- resolver el `showdown` con evaluacion real de combinaciones de poker
- repartir el bote al ganador o entre varios ganadores en caso de empate
- actualizar la mesa en tiempo real mediante `WebSockets`
- mostrar un contador de turno de `30` segundos
- retirar automaticamente al jugador si agota el tiempo
- ocultar las cartas privadas por defecto y revelarlas solo al pasar el cursor
- mostrar una puntuacion orientativa de la mano en escala `01/10` a `10/10`

## Ejecucion local

1. Crear y activar un entorno virtual.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias.

```powershell
pip install -r requirements.txt
```

3. Aplicar migraciones.

```powershell
python manage.py migrate
```

4. Arrancar el servidor de desarrollo.

```powershell
python manage.py runserver 127.0.0.1:8000
```

5. Abrir la aplicacion.

```text
http://127.0.0.1:8000/
```

## Acceso en produccion

La version desplegada del juego puede abrirse directamente en:

`www.pokervitoria.es`


