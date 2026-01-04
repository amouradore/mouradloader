document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.getElementById('urlInput');
    const getInfoBtn = document.getElementById('getInfoBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('errorMessage');
    const videoInfo = document.getElementById('videoInfo');
    const successMessage = document.getElementById('successMessage');
    const formatSelect = document.getElementById('formatSelect');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressStatus = document.getElementById('progressStatus');
    const progressSpeed = document.getElementById('progressSpeed');
    
    let currentVideoInfo = null;
    let eventSource = null;

    // Obtenir les informations de la vidéo
    getInfoBtn.addEventListener('click', async function() {
        const url = urlInput.value.trim();
        
        if (!url) {
            showError('Veuillez entrer une URL YouTube valide');
            return;
        }

        hideAll();
        loading.classList.remove('hidden');

        try {
            const response = await fetch('/get_info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok) {
                currentVideoInfo = data;
                displayVideoInfo(data);
                populateFormats(data.formats);
            } else {
                showError(data.error || 'Erreur lors de la récupération des informations');
            }
        } catch (error) {
            showError('Erreur de connexion: ' + error.message);
        } finally {
            loading.classList.add('hidden');
        }
    });

    // Télécharger la vidéo
    downloadBtn.addEventListener('click', async function() {
        const url = urlInput.value.trim();
        const downloadType = document.querySelector('input[name="downloadType"]:checked').value;
        const formatId = downloadType === 'video' ? formatSelect.value : null;

        if (!url) {
            showError('Veuillez entrer une URL YouTube valide');
            return;
        }

        hideAll();
        showProgress();

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    url: url,
                    format_id: formatId,
                    type: downloadType
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Commencer à suivre la progression
                trackProgress(data.download_id);
            } else {
                hideProgress();
                showError(data.error || 'Erreur lors du téléchargement');
            }
        } catch (error) {
            hideProgress();
            showError('Erreur de connexion: ' + error.message);
        }
    });

    // Gérer le changement de type de téléchargement
    document.querySelectorAll('input[name="downloadType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const formatSelection = document.getElementById('formatSelection');
            if (this.value === 'audio') {
                formatSelection.style.display = 'none';
            } else {
                formatSelection.style.display = 'block';
            }
        });
    });

    function displayVideoInfo(info) {
        document.getElementById('thumbnail').src = info.thumbnail;
        document.getElementById('videoTitle').textContent = info.title;
        document.getElementById('uploader').textContent = info.uploader;
        document.getElementById('duration').textContent = formatDuration(info.duration);
        
        videoInfo.classList.remove('hidden');
    }

    function populateFormats(formats) {
        formatSelect.innerHTML = '<option value="best">Meilleure qualité</option>';
        
        // Filtrer et trier les formats
        const videoFormats = formats.filter(f => f.vcodec !== 'none' && f.acodec !== 'none');
        
        videoFormats.forEach(format => {
            const option = document.createElement('option');
            option.value = format.format_id;
            const size = format.filesize ? ` (${formatFileSize(format.filesize)})` : '';
            option.textContent = `${format.quality} - ${format.ext}${size}`;
            formatSelect.appendChild(option);
        });
    }

    function formatDuration(seconds) {
        if (!seconds) return 'N/A';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        }
        return `${minutes}m ${secs}s`;
    }

    function formatFileSize(bytes) {
        if (!bytes || bytes === 0) return 'Taille inconnue';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function showSuccess(filename) {
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = `/download_file/${filename}`;
        successMessage.classList.remove('hidden');
        videoInfo.classList.remove('hidden');
    }

    function hideAll() {
        errorMessage.classList.add('hidden');
        successMessage.classList.add('hidden');
        progressContainer.classList.add('hidden');
        // Ne pas cacher videoInfo pour garder les informations visibles
    }

    function showProgress() {
        progressContainer.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        progressStatus.textContent = 'Initialisation...';
        progressSpeed.textContent = '';
    }

    function hideProgress() {
        progressContainer.classList.add('hidden');
    }

    function updateProgress(percent, status, speed) {
        progressBar.style.width = percent + '%';
        progressText.textContent = percent + '%';
        progressStatus.textContent = status;
        
        if (speed && speed > 0) {
            progressSpeed.textContent = formatSpeed(speed);
        } else {
            progressSpeed.textContent = '';
        }
    }

    function trackProgress(downloadId) {
        // Fermer la connexion précédente si elle existe
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource(`/progress/${downloadId}`);

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.status === 'starting') {
                updateProgress(0, '🚀 Démarrage du téléchargement...', 0);
            } else if (data.status === 'downloading') {
                updateProgress(data.progress, '📥 Téléchargement en cours...', data.speed);
            } else if (data.status === 'processing') {
                updateProgress(100, '⚙️ Traitement en cours...', 0);
            } else if (data.status === 'completed') {
                updateProgress(100, '✅ Téléchargement terminé!', 0);
                eventSource.close();
                
                // Récupérer le nom du fichier depuis le serveur
                fetch(`/download_result/${downloadId}`)
                    .then(response => response.json())
                    .then(result => {
                        setTimeout(() => {
                            hideProgress();
                            if (result.success && result.filename) {
                                showSuccess(result.filename);
                            } else {
                                showError('Fichier téléchargé mais nom introuvable');
                            }
                        }, 1000);
                    })
                    .catch(error => {
                        hideProgress();
                        showError('Erreur lors de la récupération du résultat');
                    });
            } else if (data.status === 'error') {
                eventSource.close();
                hideProgress();
                showError(data.error || 'Erreur lors du téléchargement');
            }
        };

        eventSource.onerror = function(error) {
            console.error('Erreur EventSource:', error);
            eventSource.close();
            hideProgress();
            showError('Erreur de connexion au serveur');
        };
    }

    function formatSpeed(bytesPerSecond) {
        if (!bytesPerSecond || bytesPerSecond === 0) return '';
        
        const speeds = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
        const i = Math.floor(Math.log(bytesPerSecond) / Math.log(1024));
        const speed = (bytesPerSecond / Math.pow(1024, i)).toFixed(2);
        
        return `${speed} ${speeds[i]}`;
    }

    // Permettre d'appuyer sur Entrée pour obtenir les infos
    urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            getInfoBtn.click();
        }
    });
});
