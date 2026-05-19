from datetime import datetime
from pathlib import Path

from database.mongo import drawings_collection


def save_drawing(user_id, drawing_name, image_path):
    drawing = {
        "user_id": str(user_id),
        "drawing_name": drawing_name,
        # Guarda siempre con slashes para que web_gallery lo lea igual
        # en Windows y Linux/Docker
        "image_path": Path(image_path).as_posix(),
        "created_at": datetime.utcnow(),
    }
    result = drawings_collection.insert_one(drawing)
    return result.inserted_id