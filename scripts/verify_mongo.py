import base64
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.storage import get_repository


PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def main():
    drawings_dir = Path("drawings")
    drawings_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = drawings_dir / f"mongo_verify_{timestamp}.png"
    output_path.write_bytes(base64.b64decode(PNG_1X1))

    repository = get_repository()
    if not repository.is_available():
        print("MongoDB no esta disponible con la URI configurada.")
        print("Revisa MONGO_URI y que Docker Compose este levantado.")
        return 1

    title = "Verificacion MongoDB"
    document = repository.save_drawing(output_path, 1, 1, title)
    if not document:
        print("No se pudo guardar metadata en MongoDB.")
        return 1

    print("MongoDB OK.")
    print(f"Archivo de prueba: {output_path}")
    print(f"Documento guardado: {document.get('filename')} - {document.get('title')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
