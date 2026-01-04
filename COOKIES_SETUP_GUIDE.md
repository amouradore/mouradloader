# 🍪 Guide: Ajouter les cookies YouTube pour contourner la détection de bot

## ⚠️ Pourquoi les cookies sont nécessaires ?
YouTube bloque maintenant les téléchargements depuis les serveurs cloud en demandant une vérification "Je ne suis pas un robot". Les cookies d'authentification permettent de contourner ce blocage.

---

## 📋 ÉTAPE 1 : Exporter vos cookies YouTube

### Méthode Recommandée : Extension Chrome "Get cookies.txt LOCALLY"

1. **Installez l'extension** :
   - Lien : https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Alternative pour Firefox : https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. **Connectez-vous à YouTube** :
   - Allez sur https://www.youtube.com
   - Connectez-vous avec votre compte Google

3. **Exportez les cookies** :
   - Cliquez sur l'icône de l'extension dans votre navigateur
   - Cliquez sur "Export" ou "Export As"
   - Un fichier 'cookies.txt' sera téléchargé

4. **Renommez le fichier** :
   - Renommez 'cookies.txt' en 'youtube_cookies.txt'
   - Placez-le dans le dossier de ce projet

---

## 📋 ÉTAPE 2 : Uploader les cookies sur Render

### Via le Dashboard Render :

1. **Allez sur votre service** :
   - https://dashboard.render.com/
   - Cliquez sur votre service 'mouradloader'

2. **Créer un fichier secret** :
   - Dans le menu à gauche, cliquez sur 'Environment'
   - Faites défiler vers 'Secret Files'
   - Cliquez sur 'Add Secret File'

3. **Configurez le fichier** :
   - **Filename** : \youtube_cookies.txt\
   - **Contents** : Copiez-collez le contenu de votre fichier youtube_cookies.txt
   - Cliquez sur 'Save Changes'

4. **Redéployez** :
   - Render va automatiquement redéployer votre application
   - Attendez 3-5 minutes que le déploiement se termine

---

## 📋 ÉTAPE 3 : Tester l'application

1. Attendez que le déploiement soit terminé (statut "Live" en vert)

2. Allez sur : https://mouradloader.onrender.com/

3. Testez avec une vidéo YouTube

4. ✅ Ça devrait fonctionner maintenant !

---

## 🔄 Renouvellement des cookies

Les cookies YouTube expirent généralement après quelques semaines/mois. Si l'erreur revient :

1. Re-exportez vos cookies (étape 1)
2. Mettez à jour le fichier secret sur Render (étape 2)
3. Redéployez

---

## 🛟 Dépannage

### L'erreur persiste après ajout des cookies ?

1. **Vérifiez que vous êtes connecté à YouTube** dans votre navigateur
2. **Re-exportez les cookies** (ils peuvent avoir expiré)
3. **Vérifiez le nom du fichier** : doit être exactement \youtube_cookies.txt\
4. **Vérifiez les logs Render** : https://dashboard.render.com/ → votre service → Logs

### Format du fichier cookies.txt

Le fichier doit être au format Netscape. Il ressemble à ceci :
\\\
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	VISITOR_INFO1_LIVE	xxxxx
.youtube.com	TRUE	/	TRUE	1234567890	YSC	xxxxx
\\\

---

## ✅ Prochaines étapes

Une fois les cookies configurés :
- Votre application fonctionnera normalement
- Les téléchargements YouTube seront possibles
- Vous devrez renouveler les cookies périodiquement

Bon téléchargement ! 🎉
