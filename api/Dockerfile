# Correction de l'erreur du tag inexistant. python:3.11-slim est valide.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping telnet dnsutils curl \
    libpq-dev gcc
RUN rm -rf /var/lib/apt/lists/*

# Configuration de l'utilisateur non-root pour la sécurité
ARG APP_USER=appuser
ENV API_PORT=5000

# Création de l'utilisateur
RUN groupadd -r ${APP_USER} && useradd --no-create-home -r -g ${APP_USER} ${APP_USER}

WORKDIR /app

# Installation des dépendances (Flask et Gunicorn)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Correction de l'erreur de Permission Denied
# 1. Création du dossier /logs en tant que root (qui a les privilèges)
# 2. Transfert de la propriété du dossier /logs à notre utilisateur non-root.
RUN mkdir -p /logs && chown -R ${APP_USER}:${APP_USER} /logs

# Changement d'utilisateur pour le principe du moindre privilège
USER ${APP_USER}

# Copie du code applicatif
COPY app.py .

# Configuration du Healthcheck


# Lancement en mode production avec Gunicorn (Corrige le Warning)
# -w 4: 4 workers pour la concurrence
# app:app: Charge l'objet 'app' du fichier 'app.py'
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
