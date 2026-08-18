# CLIDriLL v3 — single-container FastAPI app, static frontend included.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY content/ content/
COPY frontend/ frontend/

# /data holds the SQLite file so it survives rebuilds via a named volume
# (docker-compose.yml). content_decks_dir/frontend_dir in app/config.py
# resolve relative to /app, matching the COPYs above, so no env override
# is needed for those.
ENV DATABASE_URL=sqlite:////data/clidrill.db
RUN useradd --create-home --uid 1000 clidrill \
    && mkdir -p /data \
    && chown -R clidrill:clidrill /app /data
USER clidrill

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
