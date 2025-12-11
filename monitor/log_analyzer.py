import time
import re
import os

# Nom du fichier de logs NGINX monté dans le volume
LOG_FILE_PATH = os.path.join(os.getcwd(), 'logs', 'access.log')
# Expression régulière pour analyser les lignes de log (format common log format)
# Cette regex capture l'IP, la méthode, le chemin et le code de statut.
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+).*?"(?P<method>\w+)\s(?P<path>[^?]*).*?"\s(?P<status>\d{3})'
)

# Fonction pour initialiser le fichier de logs (nécessaire si le fichier n'existe pas encore)
def initialize_log_file():
    """Crée le fichier de logs s'il n'existe pas."""
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(LOG_FILE_PATH):
        # Le volume logs_vol est créé au premier mount, mais le fichier access.log doit exister pour tail
        with open(LOG_FILE_PATH, 'w') as f:
            f.write('')
    # print(f"Le fichier de logs est initialisé : {LOG_FILE_PATH}", flush=True)

def analyze_logs():
    """Lit les nouvelles lignes du fichier de logs et analyse les données."""
    
    # Dictionnaire pour stocker les statistiques de base
    stats = {
        'total_requests': 0,
        'status_codes': {},
        'path_counts': {},
    }
    
    # Utilisation de 'tail -f' équivalent en Python (lecture incrémentale)
    try:
        # Ouvre le fichier en mode lecture (r)
        with open(LOG_FILE_PATH, 'r') as f:
            # Va à la fin du fichier avant de commencer la boucle
            f.seek(0, os.SEEK_END)
            
            print("--- Moniteur de Logs Démarré ---", flush=True)
            
            while True:
                # Lit les nouvelles lignes
                new_line = f.readline()
                
                if not new_line:
                    # Rien de nouveau, attend 5 secondes avant de vérifier à nouveau
                    time.sleep(5)
                    continue
                
                # Une nouvelle ligne est trouvée, on l'analyse
                match = LOG_PATTERN.match(new_line)
                if match:
                    data = match.groupdict()
                    status = data['status']
                    path = data['path']
                    
                    stats['total_requests'] += 1
                    stats['status_codes'][status] = stats['status_codes'].get(status, 0) + 1
                    stats['path_counts'][path] = stats['path_counts'].get(path, 0) + 1
                    
                    # On affiche immédiatement le résultat de l'analyse
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] REQUÊTE ANALYSÉE | Chemin: {path}, Statut: {status}", flush=True)

    except FileNotFoundError:
        print(f"Erreur: Le fichier de logs est introuvable à {LOG_FILE_PATH}. Vérifiez le volume.", flush=True)
        time.sleep(10) # Attendre avant de réessayer
    except Exception as e:
        print(f"Une erreur inattendue s'est produite lors de l'analyse : {e}", flush=True)
        time.sleep(10)

def main():
    initialize_log_file()
    
    # On lance l'analyse dans une boucle infinie
    while True:
        # Le script analyze_logs contient déjà sa propre boucle de lecture/sleep
        analyze_logs()
        time.sleep(1) # Petit délai de sécurité entre les tentatives de lecture

if __name__ == '__main__':
    main()
