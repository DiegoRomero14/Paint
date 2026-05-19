import os

from pymongo import MongoClient

# En desarrollo local carga el .env; en Docker/Railway las variables
# ya vienen del entorno, así que el import es opcional.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise ValueError(
        "Variable de entorno MONGO_URL no encontrada. "
        "Defínela en tu .env local o en las variables del servicio."
    )

MONGO_DATABASE = os.getenv("MONGO_DATABASE", "virtual_paint")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "drawings")

client = MongoClient(MONGO_URL)
db = client[MONGO_DATABASE]
drawings_collection = db[MONGO_COLLECTION]