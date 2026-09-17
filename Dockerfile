# Utilisation d'une image Python légère
FROM python:3.11-slim

# Définition des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    PORT=8080

# Répertoire de travail
WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Création du dossier pour le volume de données persistant
RUN mkdir -p /data

# Copie du code applicatif
COPY app /app/app

# Exposition du port (8080 pour Cloud Run / Firebase, configurable via la variable $PORT)
EXPOSE 8080

# Volume persistant pour la base de données SQLite en local ou sur NAS
VOLUME ["/data"]

# Démarrage avec prise en compte dynamique de la variable $PORT de l'environnement Cloud Run / Docker
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
