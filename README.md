# Paint Virtual

Aplicacion de dibujo con la camara usando OpenCV y MediaPipe. El dedo indice dibuja sobre un canvas y los gestos de la mano cambian herramientas basicas.

## Requisitos

- Python 3.12
- Dependencias de `requirements.txt`
- Una camara disponible para usar el modo de pintura

## Instalacion

Desde la carpeta que contiene el repositorio:

```powershell
py -3.12 -m venv venv312
.\venv312\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\Paint\requirements.txt
```

## Ejecutar el Paint

```powershell
cd .\Paint
python main.py
```

Controles:

- 1 dedo: dibujar
- 2 dedos: color rojo
- 3 dedos: color verde
- 4 dedos: color azul
- 5 dedos: limpiar canvas
- S: guardar dibujo en `drawings/`
- Esc: cerrar

## Ver los dibujos en la web

```powershell
python web_gallery.py
```

Luego abre:

```text
http://127.0.0.1:8000
```

La galeria muestra las imagenes guardadas en `drawings/`.
