# ---- Build stage ----
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
    
ARG TEST

# Installer les dépendances
RUN pip install --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt && \
  if [ "$TEST" = "true" ]; then \
    pip install --no-cache-dir -r requirements-dev.txt; \
  fi

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  curl && \
  pip install --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt && \
  if [ "$TEST" = "true" ]; then \
    pip install --no-cache-dir -r requirements-dev.txt; \
  fi && \
  apt-get remove -y build-essential && \
  apt-get autoremove -y && \
  rm -rf /var/lib/apt/lists/*

# ---- Runtime stage ----
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code
COPY ./entrypoint.sh /tmp/entrypoint.sh
COPY ./src /app/src
COPY ./tests /app/tests
COPY ./pytest.ini /app/pytest.ini
COPY ./.env.test /app/.env.test

RUN mkdir -p /app/data/atp

WORKDIR /app

# Pour que les imports soient résolus depuis /app
ENV PYTHONPATH=/app

# Exposer le port
EXPOSE 7860

# Healthcheck sur FastAPI
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7860/check_health || exit 1

# Utilisateur non-root pour la sécurité
RUN useradd --create-home appuser

# Give permissions to the appuser
RUN chown -R appuser:appuser /app

USER appuser

# Entrypoint (par exemple pour lancer uvicorn)
CMD ["/tmp/entrypoint.sh"]
