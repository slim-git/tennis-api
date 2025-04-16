# ---- Build stage ----
FROM python:3.11-slim-bullseye

COPY requirements.txt .
COPY requirements-dev.txt .
    
ARG TEST

# Installer les dépendances
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ "$TEST" = "true" ]; then \
      pip install --no-cache-dir -r requirements-dev.txt; \
    fi

# Installer curl pour le healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copier le code
COPY ./entrypoint.sh /tmp/entrypoint.sh
COPY ./src /app/src
COPY ./tests /app/tests

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
USER appuser

# Entrypoint (par exemple pour lancer uvicorn)
CMD ["/tmp/entrypoint.sh"]
