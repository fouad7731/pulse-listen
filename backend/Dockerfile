# Backend Pulse Listen — image pour Railway.
# On epingle Python 3.12 (stable, wheels pandas disponibles) plutot que 3.14.
FROM python:3.12-slim

WORKDIR /app

# Dependances d'abord (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code applicatif
COPY app ./app

# Railway fournit le port via $PORT. Le scheduler tourne dans le process.
ENV PULSE_SCHEDULER=1
EXPOSE 8000

# shell form pour que $PORT soit interprete (defaut 8000 en local)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
