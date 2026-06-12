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

## Prueba funcional recomendada

Para validar la version actual:

1. registrar dos o tres usuarios
2. comprobar que cada cuenta empieza con `2.000` fichas
3. abrir varias sesiones de navegador con perfiles distintos
4. crear una partida privada y copiar su codigo
5. entrar en esa partida desde otra cuenta
6. iniciar la mano y jugar varias acciones
7. comprobar que la mesa se actualiza en tiempo real
8. revisar el ranking y el perfil tras la partida

## Variables de entorno

Variables utilizadas por la aplicacion:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
DATABASE_URL
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
```

En local puede usarse SQLite sin configurar PostgreSQL. En produccion se recomienda definir `DATABASE_URL`.

## Despliegue en Render

El despliegue recomendado para una primera defensa es Render sin Docker, conectado directamente al repositorio de GitHub.

### Configuracion del servicio web

- tipo: `Web Service`
- rama: `main`
- build command:

```bash
./build.sh
```

- start command:

```bash
daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

### Variables en Render

```text
DATABASE_URL=<url interna de PostgreSQL en Render>
DJANGO_SECRET_KEY=<clave segura>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=pokervitoria.es,www.pokervitoria.es,.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://pokervitoria.es,https://www.pokervitoria.es,https://*.onrender.com
```

### Base de datos

Crear una base de datos PostgreSQL en Render y usar su `Internal Database URL` como valor de `DATABASE_URL`.

### Dominio

Una vez comprobada la URL temporal de Render, anadir los dominios personalizados:

```text
pokervitoria.es
www.pokervitoria.es
```

Despues deben configurarse los registros DNS indicados por Render en el panel del registrador del dominio o en un proveedor DNS externo.

## Actualizacion de la version desplegada

Con `Auto-Deploy` activado en Render, el flujo de actualizacion es:

1. desarrollar y probar localmente
2. ejecutar las comprobaciones basicas
3. fusionar los cambios en `main`
4. hacer `git push origin main`
5. esperar a que Render despliegue la nueva version

Comprobaciones recomendadas antes de publicar:

```powershell
python manage.py check
python manage.py migrate
python manage.py test apps.usuarios apps.partidas
```
