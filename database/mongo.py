from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise ValueError("No se encontro MONGO_URL en el archivo .env")

client = MongoClient(MONGO_URL)

db = client["paint"]

drawings_collection = db["drawings"]