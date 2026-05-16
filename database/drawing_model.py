from database.mongo import drawings_collection
from datetime import datetime

def save_drawing(user_id, drawing_name, image_path):

    drawing = {
        "user_id": str(user_id),
        "drawing_name": drawing_name,
        "image_path": str(image_path),
        "created_at": datetime.now()
    }

    result = drawings_collection.insert_one(drawing)

    return result.inserted_id