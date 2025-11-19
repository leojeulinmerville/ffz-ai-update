FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential libffi-dev tzdata sqlite3 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV TZ=Europe/Paris
EXPOSE 8000

# Railway utilise la variable PORT, sinon on utilise 8000 par défaut
# Utiliser shell form pour supporter la variable d'environnement
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
