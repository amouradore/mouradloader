from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import os
import re
from pathlib import Path
import json
import uuid
import threading
import random

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'

# Créer le dossier downloads s'il n'existe pas
Path(app.config['DOWNLOAD_FOLDER']).mkdir(exist_ok=True)

# Dictionnaire pour stocker la progression des téléchargements
download_progress = {}
download_results = {}

# Liste de proxies gratuits (HTTP/HTTPS/SOCKS5)
# Ces proxies sont publics et peuvent ne pas toujours fonctionner
FREE_PROXIES = [
    None,  # Essayer sans proxy d'abord
    'socks5://51.158.68.68:8811',
    'socks5://51.159.154.37:8811',
    'socks5://51.158.105.107:8811',
    'http://51.210.216.186:8080',
    'http://198.27.74.6:9300',
    'http://103.152.112.162:80',
]

def get_ydl_opts_with_proxy(base_opts, use_proxy=True):
    """Configure yt-dlp avec ou sans proxy"""
    opts = base_opts.copy()
    
    if use_proxy and len(FREE_PROXIES) > 1:
        # Choisir un proxy aléatoire (skip None)
        proxy = random.choice([p for p in FREE_PROXIES if p is not None])
        opts['proxy'] = proxy
        print(f"🔄 Utilisation du proxy: {proxy}")
    
    return opts

def sanitize_filename(filename):
    """Nettoie le nom de fichier pour éviter les problèmes"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename[:200]  # Limite la longueur

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    """Récupère les informations de la vidéo"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL manquante'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'socket_timeout': 20,
            'no_check_certificate': True,
        }
        
        # Ajouter les cookies si disponibles
        cookies_file = os.environ.get('YOUTUBE_COOKIES_FILE', 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        # Headers de secours
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        }
        
        # Essayer avec différents clients (Android, iOS, Web)
        clients_to_try = ['android', 'ios', 'web']
        last_error = None
        info = None
        
        for client in clients_to_try:
            try:
                current_opts = ydl_opts.copy()
                current_opts['extractor_args'] = {
                    'youtube': {
                        'player_client': [client],
                        'player_skip': ['webpage', 'configs'],
                    }
                }
                print(f"🔄 Tentative avec client: {client}")
                
                with yt_dlp.YoutubeDL(current_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    print(f"✅ Succès avec client: {client}")
                    break  # Succès, sortir de la boucle
                    
            except Exception as e:
                last_error = e
                error_str = str(e)[:150]
                print(f"❌ Échec avec client {client}: {error_str}")
                
                # Si c'est le dernier client, lever l'erreur
                if client == clients_to_try[-1]:
                    raise last_error
                continue
        
        # Si on arrive ici sans info, c'est qu'il y a eu un problème
        if info is None:
            raise Exception("Impossible de récupérer les informations avec tous les clients")
        
        # Extraire les formats disponibles
        formats = []
        if 'formats' in info:
            for f in info['formats']:
                if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                    format_info = {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'quality': f.get('format_note', 'N/A'),
                        'filesize': f.get('filesize', 0),
                        'vcodec': f.get('vcodec', 'none'),
                        'acodec': f.get('acodec', 'none'),
                    }
                    formats.append(format_info)
        
        return jsonify({
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'uploader': info.get('uploader'),
            'formats': formats,
        })
            
    except Exception as e:
        error_msg = str(e)
        # Messages d'erreur plus clairs pour l'utilisateur
        if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
            error_msg = "YouTube a bloqué la requête. L'application essaie plusieurs proxies mais ils peuvent être lents ou indisponibles. Veuillez réessayer dans quelques instants."
        elif 'timed out' in error_msg.lower():
            error_msg = "La connexion a expiré. Le proxy utilisé est trop lent. Veuillez réessayer."
        
        print(f"❌ Erreur get_info: {error_msg}")
        return jsonify({'error': error_msg}), 500

def download_video_thread(download_id, url, format_id, download_type, download_folder):
    """Fonction pour télécharger la vidéo dans un thread séparé"""
    try:
        # Hook de progression pour yt-dlp
        def progress_hook(d):
            if d['status'] == 'downloading':
                # Calculer le pourcentage
                if 'total_bytes' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    percent = 0
                
                download_progress[download_id] = {
                    'status': 'downloading',
                    'progress': round(percent, 1),
                    'speed': d.get('speed', 0),
                    'eta': d.get('eta', 0)
                }
            elif d['status'] == 'finished':
                download_progress[download_id] = {
                    'status': 'processing',
                    'progress': 100,
                    'speed': 0,
                    'eta': 0
                }
        
        # Configuration de yt-dlp
        ydl_opts = {
            'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [progress_hook],
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'socket_timeout': 20,
            'no_check_certificate': True,
        }
        
        # Ajouter les cookies si disponibles
        cookies_file = os.environ.get('YOUTUBE_COOKIES_FILE', 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        # Headers de secours
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        }
        
        print(f"📥 Téléchargement avec clients mobiles (Android/iOS/Web)")
        
        if download_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            if format_id and format_id != 'best':
                ydl_opts['format'] = format_id
            else:
                ydl_opts['format'] = 'best'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Si c'est de l'audio, le nom de fichier change avec l'extension .mp3
            if download_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            # Marquer comme terminé
            download_progress[download_id]['status'] = 'completed'
            download_progress[download_id]['progress'] = 100
            
            # Stocker le résultat
            download_results[download_id] = {
                'success': True,
                'filename': os.path.basename(filename)
            }
            
    except Exception as e:
        error_msg = str(e)
        # Messages d'erreur plus clairs
        if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
            error_msg = "YouTube a bloqué le téléchargement. Veuillez réessayer."
        elif 'timed out' in error_msg.lower():
            error_msg = "Timeout : le proxy est trop lent. Réessayez."
        
        download_progress[download_id] = {
            'status': 'error',
            'progress': 0,
            'error': error_msg
        }
        download_results[download_id] = {
            'success': False,
            'error': error_msg
        }

@app.route('/download', methods=['POST'])
def download():
    """Télécharge la vidéo avec suivi de progression"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_id = data.get('format_id', 'best')
        download_type = data.get('type', 'video')  # 'video' ou 'audio'
        
        if not url:
            return jsonify({'error': 'URL manquante'}), 400
        
        # Générer un ID unique pour ce téléchargement
        download_id = str(uuid.uuid4())
        download_progress[download_id] = {
            'status': 'starting',
            'progress': 0,
            'speed': 0,
            'eta': 0
        }
        
        # Démarrer le téléchargement dans un thread séparé
        thread = threading.Thread(
            target=download_video_thread,
            args=(download_id, url, format_id, download_type, app.config['DOWNLOAD_FOLDER'])
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'download_id': download_id,
            'message': 'Téléchargement démarré'
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<download_id>')
def progress(download_id):
    """Endpoint pour suivre la progression d'un téléchargement"""
    def generate():
        while True:
            if download_id in download_progress:
                data = download_progress[download_id]
                yield f"data: {json.dumps(data)}\n\n"
                
                # Si terminé ou erreur, arrêter le stream
                if data['status'] in ['completed', 'error']:
                    # Nettoyer après 5 secondes
                    import time
                    time.sleep(5)
                    if download_id in download_progress:
                        del download_progress[download_id]
                    break
            else:
                yield f"data: {json.dumps({'status': 'unknown', 'progress': 0})}\n\n"
                break
            
            import time
            time.sleep(0.5)  # Mise à jour toutes les 0.5 secondes
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/download_result/<download_id>')
def download_result(download_id):
    """Récupère le résultat d'un téléchargement"""
    if download_id in download_results:
        result = download_results[download_id]
        # Nettoyer après récupération
        del download_results[download_id]
        return jsonify(result)
    else:
        return jsonify({'success': False, 'error': 'Résultat non trouvé'}), 404

@app.route('/download_file/<filename>')
def download_file(filename):
    """Envoie le fichier téléchargé au client"""
    try:
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
