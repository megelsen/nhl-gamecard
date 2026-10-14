FROM python:3.11.17-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --system --uid 10001 --no-create-home app
COPY . .
# cache/ is relative to the CWD (cache_utils.py); mount a volume here to keep it across restarts
RUN mkdir -p /app/cache && chown app:app /app/cache
USER app

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/health', timeout=4)"

# No --bind: gunicorn binds 0.0.0.0:$PORT (Render sets its own PORT).
# --preload imports the app once in the master, so the APScheduler started in app.py
# runs only there instead of once per worker.
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "30", \
     "--max-requests", "1000", "--max-requests-jitter", "100", \
     "--preload", "--access-logfile", "-", "app:app"]
