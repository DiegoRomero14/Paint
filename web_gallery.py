import os
from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from core.storage import get_repository


HOST = os.getenv("GALLERY_HOST", "127.0.0.1")
PORT = int(os.getenv("GALLERY_PORT", "8000"))
PUBLIC_URL = os.getenv("GALLERY_PUBLIC_URL", f"http://{HOST}:{PORT}")
DRAWINGS_DIR = Path("drawings")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def list_drawings():
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        file
        for file in DRAWINGS_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(files, key=lambda file: file.stat().st_mtime, reverse=True)


def list_drawing_cards():
    files = {file.name: file for file in list_drawings()}
    repository = get_repository()
    records = repository.list_drawings()

    cards = []
    for record in records:
        file = files.pop(record.get("filename", ""), None)
        if file is not None:
            cards.append({"file": file, "record": record})

    cards.extend({"file": file, "record": None} for file in files.values())
    return cards


def render_gallery():
    drawings = list_drawing_cards()

    if drawings:
        cards = "\n".join(render_card(item["file"], item["record"]) for item in drawings)
    else:
        cards = """
        <section class="empty">
            <h2>No hay dibujos guardados</h2>
            <p>Abre el paint, dibuja algo y presiona S para guardarlo.</p>
        </section>
        """

    return f"""<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Galeria de dibujos</title>
    <style>
        :root {{
            color-scheme: light;
            font-family: Arial, Helvetica, sans-serif;
            background: #f4f5f7;
            color: #202124;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            background: #f4f5f7;
        }}

        header {{
            border-bottom: 1px solid #d9dde3;
            background: #ffffff;
        }}

        .header-inner {{
            width: min(1120px, calc(100% - 32px));
            margin: 0 auto;
            padding: 24px 0 20px;
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 16px;
        }}

        h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }}

        .count {{
            margin-top: 6px;
            color: #5f6368;
            font-size: 14px;
        }}

        .refresh {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 36px;
            padding: 0 14px;
            border: 1px solid #c7cdd6;
            border-radius: 6px;
            background: #ffffff;
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
            background: #ffffff;
        }}

        .card a {{
            display: block;
            color: inherit;
            text-decoration: none;
        }}

        .preview {{
            display: block;
            width: 100%;
            aspect-ratio: 4 / 3;
            object-fit: contain;
            background: #111111;
        }}

        .meta {{
            padding: 12px;
            border-top: 1px solid #eef0f3;
        }}

        .name {{
            overflow-wrap: anywhere;
            font-size: 14px;
            font-weight: 700;
        }}

        .date {{
            margin-top: 4px;
            color: #5f6368;
            font-size: 13px;
        }}

        .empty {{
            padding: 44px 24px;
            border: 1px dashed #b8bec8;
            border-radius: 8px;
            background: #ffffff;
            text-align: center;
        }}

        .empty h2 {{
            margin: 0 0 8px;
            font-size: 22px;
        }}

        .empty p {{
            margin: 0;
            color: #5f6368;
        }}

        @media (max-width: 640px) {{
            .header-inner {{
                align-items: start;
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <div>
                <h1>Galeria de dibujos</h1>
                <div class="count">{len(drawings)} archivo(s) en drawings/</div>
            </div>
            <a class="refresh" href="/">Actualizar</a>
        </div>
    </header>
    <main>
        <div class="grid">
            {cards}
        </div>
    </main>
</body>
</html>"""


def render_card(file, record=None):
    name = escape(file.name)
    title = escape(record.get("title", file.stem) if record else file.stem)
    image_url = "/drawings/" + quote(file.name)
    created_at = record.get("created_at") if record else None
    modified = file.stat().st_mtime
    modified_text = (
        format_datetime(created_at)
        if created_at
        else datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M")
    )
    dimensions = format_dimensions(record)
    size = format_size(record.get("size_bytes") if record else file.stat().st_size)
    details = " - ".join(part for part in [modified_text, dimensions, size] if part)

    return f"""
    <article class="card">
        <a href="{image_url}" target="_blank" rel="noreferrer">
            <img class="preview" src="{image_url}" alt="{name}">
            <div class="meta">
                <div class="name">{title}</div>
                <div class="date">{details}</div>
                <div class="date">{name}</div>
            </div>
        </a>
    </article>
    """


def format_datetime(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def format_dimensions(record):
    if not record:
        return ""

    width = record.get("width")
    height = record.get("height")
    if not width or not height:
        return ""

    return f"{width}x{height}"


def format_size(size_bytes):
    if not size_bytes:
        return ""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    return f"{size_bytes / 1024:.1f} KB"


class GalleryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.send_html(render_gallery())
            return

        if path.startswith("/drawings/"):
            self.send_drawing(path)
            return

        self.send_error(404, "No encontrado")

    def send_html(self, html):
        content = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_drawing(self, path):
        filename = Path(unquote(path.removeprefix("/drawings/"))).name
        file_path = DRAWINGS_DIR / filename

        if not file_path.exists() or file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            self.send_error(404, "Imagen no encontrada")
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.content_type_for(file_path))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def content_type_for(self, file_path):
        extension = file_path.suffix.lower()
        if extension in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if extension == ".webp":
            return "image/webp"
        return "image/png"


def main():
    server = ThreadingHTTPServer((HOST, PORT), GalleryHandler)
    print(f"Galeria disponible en {PUBLIC_URL}")
    print("Presiona Ctrl+C para cerrar el servidor.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor cerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
