# Paint Virtual

Aplicacion de dibujo con la camara usando OpenCV y MediaPipe. El dedo indice dibuja sobre un canvas y los gestos de la mano cambian herramientas basicas.

## Mejoras incluidas

- Guardado de dibujos en `drawings/` con metadata opcional en MongoDB.
- Galeria web que muestra imagenes y, si Mongo esta activo, tambien resolucion y tamano.
- Reconocimiento de gestos mas estable, con suavizado adaptativo y menos trazos accidentales.
- Dialogo dentro del paint para nombrar el dibujo al guardar con `S`.
- Cluster local de MongoDB con 3 nodos en replica set usando Docker Compose.
- Dockerfile para ejecutar la galeria web en contenedor.
- El paint sigue funcionando sin Mongo para facilitar pruebas en clase.

## Requisitos

- Python 3.12
- Dependencias de `requirements.txt`
- Una camara disponible para usar el modo de pintura
- Docker Desktop, si quieres levantar MongoDB y la galeria en contenedores

## Instalacion

Desde la carpeta que contiene el repositorio:

```powershell
py -3.12 -m venv venv312
.\venv312\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
```

## Ejecutar el Paint

```powershell
python main.py
```

`main.py` es la unica entrada principal del proyecto.

## Arquitectura usada

El proyecto usa una arquitectura modular por capas:

- Entrada: `main.py` y `web_gallery.py`
- Logica: `core/gestures.py` y `core/painter.py`
- Integraciones: `core/camara.py`, `core/hand_tracker.py` y `core/storage.py`
- Infraestructura: `Dockerfile`, `docker-compose.yml`, MongoDB y `drawings/`

Mas detalle en `docs/ARCHITECTURE.md`.

Controles:

- Solo indice: dibujar
- Indice + medio: color rojo
- Indice + medio + anular: color verde
- 4 dedos sin pulgar: color azul
- Mano abierta: limpiar canvas
- S: abrir dialogo de nombre dentro del paint
- Enter: guardar cuando estas escribiendo el nombre
- Esc: cerrar

La ventana muestra un rectangulo de zona segura. Mantener la mano dentro de esa zona mejora la deteccion; cerca de los bordes el paint pausa los gestos para evitar trazos y comandos equivocados.

Si MongoDB esta levantado, cada dibujo guardado tambien registra metadata en la coleccion `virtual_paint.drawings`.

## Ver los dibujos en la web

```powershell
python web_gallery.py
```

Luego abre:

```text
http://127.0.0.1:8000
```

La galeria muestra las imagenes guardadas en `drawings/`.

## Levantar MongoDB en cluster y la galeria con Docker

```powershell
docker compose up --build
```

O en segundo plano:

```powershell
docker compose up --build -d
```

Servicios:

- Galeria: `http://127.0.0.1:8000`
- Mongo nodo 1: `localhost:27017`
- Mongo nodo 2: `localhost:27018`
- Mongo nodo 3: `localhost:27019`

La URI del cluster usada por Docker es:

```text
MONGO_URL=mongodb+srv://kexxx04_db_user:<db_password>@paint.x5sghao.mongodb.net/?appName=Paint
```

Docker levanta la galeria y MongoDB. El paint principal no se ejecuta dentro de Docker porque `main.py` usa webcam y ventana grafica de OpenCV; en Windows eso funciona mejor ejecutandolo localmente.

Para que el paint local guarde metadata en ese mismo cluster, ejecuta antes de `python main.py`:

```powershell
$env:MONGO_URI="mongodb://localhost:27017/?directConnection=true"
$env:MONGO_DATABASE="virtual_paint"
python main.py
```

Luego abre el paint, guarda con `S` y refresca la galeria. Desde tu maquina se usa conexion directa al nodo expuesto en `27017`; dentro de Docker la galeria si usa la URI completa del replica set con los nombres `mongo1`, `mongo2` y `mongo3`.

Para revisar que los contenedores estan arriba:

```powershell
docker compose ps
```

Para ver logs de la galeria:

```powershell
docker compose logs -f gallery
```

Para verificar MongoDB sin abrir la camara:

```powershell
$env:MONGO_URL=mongodb+srv://kexxx04_db_user:<db_password>@paint.x5sghao.mongodb.net/?appName=Paint
python .\scripts\verify_mongo.py
```

Si funciona, veras `MongoDB OK.` y se creara una imagen de prueba en `drawings/`.

## Usar MongoDB de Docker

El proyecto esta configurado para usar el MongoDB local de Docker por defecto. Si quieres fijarlo manualmente, crea un archivo `.env` en la raiz:

```env
MONGO_URL=mongodb+srv://kexxx04_db_user:<db_password>@paint.x5sghao.mongodb.net/?appName=Paint
```

Luego prueba la conexion contra el contenedor:

```powershell
python .\scripts\verify_mongo.py
```

Si funciona, MongoDB Compass debe conectarse con:

```text
mongodb://localhost:27017/?directConnection=true
```

Y debes ver:

```text
virtual_paint
└── drawings
```

## Ideas para mejorar el proyecto aun mas

- Agregar modo borrador, grosor de pincel por gesto y selector visual de herramienta.
- Crear pruebas unitarias para `core/gestures.py`, `core/storage.py` y la galeria.
- Cambiar la galeria a Flask o FastAPI si necesitas API REST, login o endpoints para estadisticas.
- Agregar exportacion por fecha, busqueda y borrado controlado de dibujos desde la web.
