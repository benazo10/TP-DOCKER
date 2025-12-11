import time
import os
import traceback 
from flask import Flask, jsonify, request, Response
import psycopg2

# --- IMPORTATIONS PROMETHEUS ---
from prometheus_client import generate_latest, Counter, Histogram, Gauge

app = Flask(__name__)

# --- CHEMIN DU SECRET DOCKER SWARM ---
DB_PASSWORD_FILE = '/run/secrets/tp_db_password'

# --- DÉFINITION DES MÉTRIQUES ---
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP Requests', ['method', 'endpoint']
)
REQUEST_LATENCY = Histogram(
    'http_request_latency_seconds', 'HTTP Request Latency', ['endpoint']
)
DB_STATUS = Gauge('db_connection_status', 'Database connection status (1=up, 0=down)')


# --- MIDDLEWARE POUR LES METRIQUES ---
@app.before_request
def before_request_func():
    """Enregistre le temps de début de la requête."""
    request.start_time = time.time()

@app.after_request
def after_request_func(response):
    """Enregistre les métriques après la requête."""
    endpoint = request.path
    REQUEST_COUNT.labels(request.method, endpoint).inc()
    
    latency = time.time() - request.start_time
    REQUEST_LATENCY.labels(endpoint).observe(latency)
    
    return response


# --- ROUTES DE L'APPLICATION ---

# Route Racine (Modification pour le Rolling Update - v2.0)
@app.route('/')
def home():
    """Affiche un message de succès simple pour valider l'accès via NGINX."""
    # Mettez ici le message de votre version actuelle (ex: v1.0 ou v2.0)
    return "Service API v2.0 is running successfully!", 200

# Route de santé du service
@app.route('/health')
def health_check():
    """Retourne l'état du serveur API."""
    return jsonify({"status": "healthy"}), 200

# Route de vérification de la connexion à la Base de Données
@app.route('/db-health')
def db_health_check():
    """Tente d'établir et de fermer une connexion à la DB, en lisant le secret."""
    
    db_host = os.environ.get('DB_HOST', 'db')
    db_name = os.environ.get('DB_NAME', 'tp_db')
    db_user = os.environ.get('DB_USER', 'user_app')

    # --- LOGIQUE CRITIQUE : LECTURE DU SECRET SWARM ---
    db_password = None
    try:
        # Tente de lire le mot de passe depuis le fichier injecté par Swarm
        with open(DB_PASSWORD_FILE, 'r') as f:
            db_password = f.read().strip()
    except FileNotFoundError:
        # Si le fichier secret n'est pas trouvé (ex: mode local ou secret non injecté)
        # on essaie de le lire dans une variable d'environnement (pour compatibilité)
        db_password = os.environ.get('DB_PASSWORD', 'secret_password_fallback') 
    
    if not db_password or db_password == 'secret_password_fallback':
        # Si la lecture du secret échoue ou si le mot de passe est celui de fallback
        return jsonify({
            "db_status": "configuration_error",
            "error": "DB password secret file not found or empty.",
            "service": "degraded"
        }), 500
    # ---------------------------------------------------

    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password # Utilise le mot de passe lu du secret
        )
        conn.close()
        DB_STATUS.set(1) # Met la jauge à 1 (UP)
        return jsonify({"db_status": "connected", "service": "operational"}), 200
        
    except psycopg2.Error as e:
        DB_STATUS.set(0) # Met la jauge à 0 (DOWN)
        return jsonify({
            "db_status": "disconnected",
            "error": str(e),
            "service": "degraded"
        }), 503

# Route pour Prometheus (métriques)
@app.route('/metrics')
def metrics():
    """Expose les métriques Prometheus."""
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
