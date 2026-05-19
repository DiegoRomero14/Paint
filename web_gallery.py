import os
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from database.mongo import drawings_collection


HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8000"))
PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", f"http://{HOST}:{PORT}")
DRAWINGS_DIR = Path("drawings")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def list_drawing_cards():
    drawings = list(drawings_collection.find().sort("created_at", -1))
    cards = []
    for drawing in drawings:
        raw_path = drawing.get("image_path", "")
        # Normaliza backslashes de Windows y extrae solo el nombre del archivo
        filename = Path(str(raw_path).replace("\\", "/")).name
        cards.append({
            "name": drawing.get("drawing_name", "Sin nombre"),
            "filename": filename,
            "created_at": drawing.get("created_at"),
        })
    return cards


def format_datetime(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value) if value else ""


def render_card(item):
    filename = escape(item["filename"])
    name = escape(item["name"])
    date = format_datetime(item["created_at"])
    return f"""
    <article class="card">
        <a href="/drawings/{filename}" target="_blank">
            <img class="preview" src="/drawings/{filename}" alt="{name}">
            <div class="meta">
                <div class="name">{name}</div>
                <div class="date">{date}</div>
            </div>
        </a>
    </article>"""


def render_gallery():
    drawings = list_drawing_cards()
    cards_html = "\n".join(render_card(item) for item in drawings) if drawings else """
        <section class="empty">
            <h2>No hay dibujos guardados</h2>
            <p>Abre el paint, dibuja algo y presiona S para guardarlo.</p>
        </section>"""

    return f"""<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Galeria de dibujos</title>
    <style>
        :root {{
            font-family: Arial, Helvetica, sans-serif;
            background: #f4f5f7;
            color: #202124;
        }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; min-height: 100vh; }}
        header {{ border-bottom: 1px solid #d9dde3; background: #fff; }}
        .header-inner {{
            width: min(1120px, calc(100% - 32px));
            margin: 0 auto;
            padding: 24px 0 20px;
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 16px;
        }}
        h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
        .count {{ margin-top: 6px; color: #5f6368; font-size: 14px; }}
        .refresh {{
            display: inline-flex;
            align-items: center;
            min-height: 36px;
            padding: 0 14px;
            border: 1px solid #c7cdd6;
            border-radius: 6px;
            background: #fff;
            color: #202124;
            text-decoration: none;
            font-size: 14px;
        }}
        main {{
            width: min(1120px, calc(100% - 32px));
            margin: 28px auto;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 18px;
        }}
        .card {{
            overflow: hidden;
            border: 1px solid #d9dde3;
            border-radius: 8px;
            background: #fff;
        }}
        .card a {{ display: block; color: inherit; text-decoration: none; }}
        .preview {{
            display: block;
            width: 100%;
            aspect-ratio: 4 / 3;
            object-fit: contain;
            background: #111;
        }}
        .meta {{ padding: 12px; border-top: 1px solid #eef0f3; }}
        .name {{ overflow-wrap: anywhere; font-size: 14px; font-weight: 700; }}
        .date {{ margin-top: 4px; color: #5f6368; font-size: 13px; }}
        .empty {{
            padding: 44px 24px;
            border: 1px dashed #b8bec8;
            border-radius: 8px;
            background: #fff;
            text-align: center;
        }}
        .empty h2 {{ margin: 0 0 8px; font-size: 22px; }}
        .empty p {{ margin: 0; color: #5f6368; }}
        @media (max-width: 640px) {{
            .header-inner {{ align-items: start; flex-direction: column; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <div>
                <h1>Galeria de dibujos</h1>
                <div class="count">{len(drawings)} dibujo(s)</div>
            </div>
            <a class="refresh" href="/">Actualizar</a>
        </div>
    </header>
    <main>
        <div class="grid">{cards_html}</div>
    </main>
</body>
</html>"""


class GalleryHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silencia el log de cada request en producción
        pass

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.send_html(render_gallery())
            return

        if path.startswith("/drawings/"):
            self.serve_image(path)
            return

        self.send_error(404, "No encontrado")

    def send_html(self, html):
        content = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_image(self, path):
        filename = Path(unquote(path.removeprefix("/drawings/"))).name
        file_path = DRAWINGS_DIR / filename

        if not file_path.exists() or file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            self.send_error(404, "Imagen no encontrada")
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self._content_type(file_path))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _content_type(self, file_path):
        ext = file_path.suffix.lower()
        return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext.lstrip("."), "image/png")


def main():
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), GalleryHandler)
    print(f"Galeria disponible en {PUBLIC_URL}")
    print("Presiona Ctrl+C para cerrar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor cerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()