import os
import secrets
from datetime import datetime
from html import escape
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse


HOST = os.getenv("GALLERY_HOST", "127.0.0.1")
PORT = int(os.getenv("GALLERY_PORT", "8000"))
PUBLIC_URL = os.getenv("GALLERY_PUBLIC_URL", f"http://{HOST}:{PORT}")
DRAWINGS_DIR = Path("drawings")
TEMPLATES_DIR = Path("templates")
STATIC_DIR = Path("static")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SESSION_COOKIE = "paint_gallery_session"
SESSION_MAX_AGE = 60 * 60 * 8
SESSIONS = {}


def read_template(template_name):
    return (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")


def render_template(template_name, **context):
    content = read_template(template_name)

    for key, value in context.items():
        content = content.replace(f"{{{{ {key} }}}}", str(value))

    return content


def create_session(email):
    display_name = email.split("@", 1)[0]
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {
        "email": email,
        "display_name": display_name,
        "initials": display_name[:2],
    }
    return token


def get_session_from_headers(headers):
    cookie_header = headers.get("Cookie")
    if not cookie_header:
        return None

    jar = cookies.SimpleCookie()
    jar.load(cookie_header)
    morsel = jar.get(SESSION_COOKIE)
    if not morsel:
        return None

    return SESSIONS.get(morsel.value)


def expire_session_from_headers(headers):
    cookie_header = headers.get("Cookie")
    if not cookie_header:
        return

    jar = cookies.SimpleCookie()
    jar.load(cookie_header)
    morsel = jar.get(SESSION_COOKIE)
    if morsel:
        SESSIONS.pop(morsel.value, None)


def build_session_cookie(token):
    return (
        f"{SESSION_COOKIE}={token}; "
        f"Path=/; Max-Age={SESSION_MAX_AGE}; HttpOnly; SameSite=Lax"
    )


def build_expired_cookie():
    return f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"


def validate_login(email, password):
    email = email.strip().lower()

    if not email:
        return None, "Ingresa tu correo o usuario."
    if len(password) < 4:
        return None, "La contrasena debe tener al menos 4 caracteres."

    expected_password = os.getenv("GALLERY_LOGIN_PASSWORD")
    if expected_password and password != expected_password:
        return None, "Credenciales invalidas."

    return email, None


def get_mongo_documents():
    uri = os.getenv("MONGO_URI") or os.getenv("MONGO_URL")
    if not uri:
        return [], "archivos locales"

    try:
        from pymongo import MongoClient
    except ImportError:
        return [], "archivos locales"

    timeout_ms = int(os.getenv("MONGO_TIMEOUT_MS", "1200"))
    collection_name = os.getenv("MONGO_COLLECTION", "drawings")
    configured_db = os.getenv("MONGO_DATABASE")
    db_names = [configured_db] if configured_db else ["virtual_paint", "paint"]

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        client.admin.command("ping")

        for db_name in db_names:
            documents = list(
                client[db_name][collection_name].find().sort("created_at", -1)
            )
            if documents:
                return documents, f"MongoDB ({db_name}.{collection_name})"
    except Exception:
        return [], "archivos locales"

    return [], "archivos locales"


def list_local_drawings():
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        file
        for file in DRAWINGS_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(files, key=lambda file: file.stat().st_mtime, reverse=True)


def list_gallery_items():
    documents, source = get_mongo_documents()
    items = [gallery_item_from_document(document) for document in documents]
    items = [item for item in items if item]

    if items:
        return items, source

    return [gallery_item_from_file(file) for file in list_local_drawings()], source


def gallery_item_from_document(document):
    image_path = str(document.get("image_path", ""))
    image_name = Path(image_path.replace("\\", "/")).name
    if not image_name:
        return None

    file_path = DRAWINGS_DIR / image_name
    return {
        "name": document.get("drawing_name", "Sin nombre"),
        "image_url": "/drawings/" + quote(image_name),
        "created_at": document.get("created_at"),
        "size": file_path.stat().st_size if file_path.exists() else None,
    }


def gallery_item_from_file(file_path):
    return {
        "name": file_path.stem,
        "image_url": "/drawings/" + quote(file_path.name),
        "created_at": datetime.fromtimestamp(file_path.stat().st_mtime),
        "size": file_path.stat().st_size,
    }


def render_gallery(user):
    drawings, source = list_gallery_items()
    cards = "\n".join(render_card(item) for item in drawings)

    if not cards:
        cards = read_template("empty_state.html")

    return render_template(
        "gallery.html",
        cards=cards,
        count=len(drawings),
        source=escape(source),
        user_email=escape(user["email"]),
        user_name=escape(user["display_name"]),
        user_initials=escape(user["initials"]),
    )


def render_login(error="", email=""):
    return render_template(
        "login.html",
        error=render_login_error(error),
        email=escape(email),
    )


def render_login_error(error):
    if not error:
        return ""

    return render_template("form_error.html", error=escape(error))


def render_card(item):
    return render_template(
        "drawing_card.html",
        name=escape(item["name"]),
        image_url=escape(item["image_url"]),
        created_at=escape(format_datetime(item.get("created_at"))),
        size=escape(format_size(item.get("size"))),
    )


def format_datetime(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    if value:
        return str(value)
    return "Fecha no disponible"


def format_size(size_bytes):
    if not size_bytes:
        return "Tamano no disponible"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    return f"{size_bytes / 1024:.1f} KB"


class GalleryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        user = get_session_from_headers(self.headers)

        if path == "/login":
            if user:
                self.redirect("/")
                return
            self.send_html(render_login())
            return

        if path == "/logout":
            expire_session_from_headers(self.headers)
            self.redirect("/login", extra_headers={"Set-Cookie": build_expired_cookie()})
            return

        if path.startswith("/static/"):
            self.send_static(path)
            return

        if not user:
            self.redirect("/login")
            return

        if path == "/":
            self.send_html(render_gallery(user))
            return

        if path.startswith("/drawings/"):
            self.send_drawing(path)
            return

        self.send_error(404, "No encontrado")

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/login":
            self.send_error(404, "No encontrado")
            return

        form = self.read_form()
        email = form.get("email", [""])[0]
        password = form.get("password", [""])[0]
        valid_email, error = validate_login(email, password)

        if error:
            self.send_html(render_login(error=error, email=email), status=400)
            return

        token = create_session(valid_email)
        self.redirect("/", extra_headers={"Set-Cookie": build_session_cookie(token)})

    def read_form(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        content = self.rfile.read(content_length).decode("utf-8")
        return parse_qs(content)

    def redirect(self, location, extra_headers=None):
        self.send_response(302)
        self.send_header("Location", location)
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()

    def send_html(self, html, status=200):
        content = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_static(self, path):
        filename = Path(unquote(path.removeprefix("/static/"))).name
        file_path = STATIC_DIR / filename

        if not file_path.exists():
            self.send_error(404, "Archivo no encontrado")
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.content_type_for(file_path))
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
        if extension == ".css":
            return "text/css; charset=utf-8"
        return "image/png"


def main():
    server = ThreadingHTTPServer((HOST, PORT), GalleryHandler)
    print(f"Galeria disponible en {PUBLIC_URL}")
    print("Login basico activo. Presiona Ctrl+C para cerrar el servidor.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor cerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
