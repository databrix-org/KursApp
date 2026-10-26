FROM ghcr.io/astral-sh/uv:0.9.5 AS uv
FROM python:3.11.17-slim-bookworm AS builder
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app/apps/backend
ENV UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1
COPY apps/backend/pyproject.toml apps/backend/uv.lock ./
RUN uv sync --frozen --no-dev

FROM builder AS test
RUN uv sync --frozen
COPY apps/backend/ ./
ENV PATH="/app/apps/backend/.venv/bin:$PATH" DJANGO_SETTINGS_MODULE=config.settings
CMD ["python","manage.py","test","course.tests","--noinput"]

FROM python:3.11.17-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/apps/backend/.venv/bin:$PATH" DJANGO_SETTINGS_MODULE=config.settings
RUN groupadd --gid 10001 databrix && useradd --uid 10001 --gid databrix --no-create-home databrix
WORKDIR /app/apps/backend
COPY --from=builder /app/apps/backend/.venv ./.venv
COPY --chown=10001:10001 apps/backend/ ./
RUN python manage.py collectstatic --noinput && mkdir -p /var/tmp/databrix && chown 10001:10001 /var/tmp/databrix
USER 10001:10001
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz/')"
CMD ["gunicorn","config.wsgi:application","--bind=0.0.0.0:8000","--workers=3","--timeout=90","--graceful-timeout=30","--access-logfile=-"]
