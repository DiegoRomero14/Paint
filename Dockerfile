FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-gallery.txt .
RUN pip install --no-cache-dir -r requirements-gallery.txt

COPY core ./core
COPY web_gallery.py .
RUN mkdir -p drawings

EXPOSE 8000

CMD ["python", "web_gallery.py"]
