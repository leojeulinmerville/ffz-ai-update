FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# OS deps (sqlite, tzdata)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential libffi-dev tzdata sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# timezone
ARG TZ=Europe/Paris
ENV TZ=${TZ}

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
