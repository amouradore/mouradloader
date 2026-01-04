from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import os
import re
from pathlib import Path
import json
import uuid
import threading

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'

# Créer le dossier downloads s'il n'existe pas
Path(app.config['DOWNLOAD_FOLDER']).mkdir(exist_ok=True)

# Dictionnaire pour stocker la progression des téléchargements
download_progress = {}
download_results = {}

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
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; GB) gzip',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
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
        return jsonify({'error': str(e)}), 500

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
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; GB) gzip',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
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
        download_progress[download_id] = {
            'status': 'error',
            'progress': 0,
            'error': str(e)
        }
        download_results[download_id] = {
            'success': False,
            'error': str(e)
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
