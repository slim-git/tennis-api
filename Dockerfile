FROM tiangolo/uvicorn-gunicorn:python3.11

COPY ./requirements.txt /tmp/requirements.txt
COPY ./entrypoint.sh /tmp/entrypoint.sh
COPY ./src /app/src
COPY ./tests /app/tests

RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app

ENV PYTHONPATH=/app

# Port to expose
EXPOSE 7860

# Health Check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD [ "curl", "-f", "http://localhost:7860/check_health" ]

# Create a non-root user 'appuser' and switch to this user
RUN useradd --create-home appuser
USER appuser

# CMD with JSON notation
CMD ["/tmp/entrypoint.sh"]