# 🎬 MouradLoader

Une application web moderne et élégante pour télécharger des vidéos YouTube facilement avec une barre de progression en temps réel.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Fonctionnalités

- 🎥 **Téléchargement de vidéos YouTube** en différentes qualités
- 🎵 **Extraction audio** au format MP3
- 📊 **Barre de progression en temps réel** avec pourcentage et vitesse
- 🎨 **Interface moderne et responsive** avec design gradient
- 👁️ **Prévisualisation** avec miniature et informations de la vidéo
- 🔍 **Sélection du format** pour choisir la qualité désirée
- ⚡ **Téléchargement en arrière-plan** avec Server-Sent Events

## 📸 Captures d'écran

*Interface principale avec barre de recherche*

*Prévisualisation de la vidéo avec options de téléchargement*

*Barre de progression en temps réel*

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- FFmpeg (optionnel, pour la conversion audio)

### Étapes d'installation

1. **Cloner le dépôt**
```bash
git clone https://github.com/votre-username/mouradloader.git
cd mouradloader
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Lancer l'application**
```bash
python app.py
```

4. **Accéder à l'application**
   
   Ouvrez votre navigateur et allez sur : **http://localhost:5000**

## 📖 Utilisation

1. 📋 **Copiez l'URL** d'une vidéo YouTube
2. 📌 **Collez-la** dans le champ de saisie
3. ℹ️ **Cliquez sur "Obtenir les infos"** pour voir les détails
4. 🎬 **Choisissez** entre télécharger la vidéo ou l'audio
5. 🎯 **Sélectionnez le format** souhaité (pour les vidéos)
6. 📥 **Cliquez sur "Télécharger"**
7. 📊 **Suivez la progression** en temps réel
8. 💾 **Téléchargez le fichier** une fois terminé

## 🛠️ Technologies utilisées

- **Backend** : Flask (Python)
- **Frontend** : HTML5, CSS3, JavaScript (Vanilla)
- **Téléchargement** : yt-dlp
- **Temps réel** : Server-Sent Events (SSE)
- **Threading** : Pour les téléchargements en arrière-plan

## 📁 Structure du projet

```
mouradloader/
│
├── app.py                  # Backend Flask avec API
├── requirements.txt        # Dépendances Python
├── README.md              # Documentation
├── .gitignore             # Fichiers à ignorer
│
├── templates/
│   └── index.html         # Interface utilisateur
│
├── static/
│   ├── css/
│   │   └── style.css      # Styles et animations
│   └── js/
│       └── script.js      # Logique client et EventSource
│
└── downloads/             # Dossier des fichiers téléchargés
    └── .gitkeep
```

## 🔧 Configuration

### Installation de FFmpeg (pour l'audio MP3)

**Windows:**
```bash
# Téléchargez depuis https://ffmpeg.org/download.html
# Ajoutez FFmpeg au PATH système
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

## ⚙️ API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| / | GET | Page principale |
| /get_info | POST | Récupère les infos d'une vidéo |
| /download | POST | Démarre un téléchargement |
| /progress/<id> | GET | Stream SSE de progression |
| /download_result/<id> | GET | Résultat du téléchargement |
| /download_file/<filename> | GET | Télécharge le fichier |

## ⚠️ Avertissement

Cette application est destinée à un **usage personnel et éducatif** uniquement. 

- ⚖️ Respectez les **droits d'auteur** et les conditions d'utilisation de YouTube
- 📜 Assurez-vous d'avoir les **autorisations nécessaires** avant de télécharger du contenu
- 🎓 Utilisez-la de manière **responsable** et **légale**

## 🐛 Problèmes connus

- La conversion audio nécessite FFmpeg installé
- Les très grandes vidéos peuvent prendre du temps
- Certains formats peuvent ne pas être disponibles selon la vidéo

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. 🍴 Fork le projet
2. 🔨 Créer une branche (git checkout -b feature/AmazingFeature)
3. 💾 Commit vos changements (git commit -m 'Add AmazingFeature')
4. 📤 Push vers la branche (git push origin feature/AmazingFeature)
5. 🎉 Ouvrir une Pull Request

## 📝 Roadmap

- [ ] Support des playlists YouTube
- [ ] Téléchargement de sous-titres
- [ ] Historique des téléchargements
- [ ] Mode sombre / clair
- [ ] Support multi-langues
- [ ] Application desktop avec Electron
- [ ] Support d'autres plateformes (Vimeo, Dailymotion, etc.)

## 📄 License

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👨‍💻 Auteur

**MouradLoader** - Votre solution moderne pour télécharger des vidéos YouTube

---

⭐ **Si vous aimez ce projet, n'oubliez pas de lui donner une étoile sur GitHub!** ⭐

## 💬 Support

Pour toute question ou problème, n'hésitez pas à ouvrir une [issue](https://github.com/votre-username/mouradloader/issues).
