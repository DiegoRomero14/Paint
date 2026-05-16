# Arquitectura

Este proyecto usa una arquitectura modular por capas, sencilla y adecuada para una app pequena de vision por computador:

- Capa de entrada: `main.py` y `web_gallery.py`.
- Capa de dominio/logica: `core/gestures.py` y `core/painter.py`.
- Capa de integracion: `core/camara.py`, `core/hand_tracker.py` y `core/storage.py`.
- Capa de infraestructura: `Dockerfile`, `docker-compose.yml`, MongoDB y volumen `drawings/`.

## Flujo principal

```text
Camara -> MediaPipe -> Gestos -> Painter -> PNG en drawings/
                                      -> Metadata en MongoDB

drawings/ + MongoDB -> web_gallery.py -> Galeria web
```

## Responsabilidades

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Punto de entrada unico para pintar con la camara. Coordina lectura de frames, gestos, dibujo y guardado. |
| `web_gallery.py` | Servidor web simple para mostrar los dibujos guardados. |
| `core/camara.py` | Inicializa OpenCV y configura la camara. |
| `core/hand_tracker.py` | Encapsula MediaPipe Hands y la deteccion de manos. |
| `core/gestures.py` | Interpreta landmarks como dedos levantados y gestos estables. |
| `core/painter.py` | Mantiene la logica de dibujo sobre el canvas. |
| `core/storage.py` | Guarda y consulta metadata de dibujos en MongoDB, de forma opcional. |
| `drawings/` | Almacenamiento local de imagenes generadas. |
| `docker-compose.yml` | Levanta la galeria y un cluster MongoDB replica set de 3 nodos. |

## Por que esta arquitectura

La arquitectura modular por capas evita que todo viva dentro de un solo script. Cada modulo tiene una razon clara para cambiar:

- Si falla la camara, se revisa `core/camara.py`.
- Si un gesto se detecta mal, se revisa `core/gestures.py`.
- Si el dibujo se ve mal, se revisa `core/painter.py`.
- Si MongoDB no conecta, se revisa `core/storage.py` o Docker.

Tambien deja el proyecto listo para crecer sin reescribir todo. Por ejemplo, `web_gallery.py` se puede cambiar luego por Flask o FastAPI sin tocar la logica de gestos.

## Decision sobre Docker

La galeria y MongoDB se dockerizan porque son servicios de servidor. El paint con camara se ejecuta localmente porque usa webcam y ventana grafica de OpenCV, lo cual suele ser mas estable fuera de Docker en Windows.
