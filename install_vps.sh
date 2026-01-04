#!/bin/bash

# Script d'installation automatique pour MouradLoader sur VPS Ubuntu/Debian
# Ce script installe Python, les dépendances, configure le service systemd et démarre l'application

echo "=========================================="
echo "  Installation de MouradLoader sur VPS"
echo "=========================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then 
    print_error "Ce script doit être exécuté en tant que root (utilisez sudo)"
    exit 1
fi

print_info "Mise à jour du système..."
apt update && apt upgrade -y
print_success "Système mis à jour"

print_info "Installation de Python 3 et pip..."
apt install -y python3 python3-pip python3-venv git nginx
print_success "Python et Nginx installés"

print_info "Création du dossier d'application..."
cd /opt
if [ -d "mouradloader" ]; then
    print_info "Dossier existant trouvé, mise à jour..."
    cd mouradloader
    git pull
else
    print_info "Clone du dépôt GitHub..."
    git clone https://github.com/amouradore/mouradloader.git
    cd mouradloader
fi
print_success "Code récupéré"

print_info "Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate
print_success "Environnement virtuel créé"

print_info "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dépendances installées"

print_info "Création du dossier downloads..."
mkdir -p downloads
chmod 755 downloads
print_success "Dossier downloads créé"

print_info "Configuration du service systemd..."
cat > /etc/systemd/system/mouradloader.service << 'EOF'
[Unit]
Description=MouradLoader YouTube Downloader
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mouradloader
Environment="PATH=/opt/mouradloader/venv/bin"
ExecStart=/opt/mouradloader/venv/bin/gunicorn app:app --bind 0.0.0.0:8000 --timeout 120 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
print_success "Service systemd configuré"

print_info "Configuration de Nginx comme reverse proxy..."
cat > /etc/nginx/sites-available/mouradloader << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 500M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/mouradloader /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
print_success "Nginx configuré"

print_info "Activation et démarrage des services..."
systemctl daemon-reload
systemctl enable mouradloader
systemctl restart mouradloader
systemctl restart nginx
print_success "Services démarrés"

echo ""
echo "=========================================="
print_success "Installation terminée avec succès!"
echo "=========================================="
echo ""
print_info "Votre application est maintenant accessible sur:"
echo "  👉 http://$(curl -s ifconfig.me)"
echo ""
print_info "Commandes utiles:"
echo "  • Voir les logs: journalctl -u mouradloader -f"
echo "  • Redémarrer: systemctl restart mouradloader"
echo "  • Statut: systemctl status mouradloader"
echo ""
