# Examen TEC en ligne — Guide de déploiement

## Architecture
- `examen.html` → Page étudiants (GitHub Pages)  
- `enseignant.html` → Tableau de bord enseignant (GitHub Pages)  
- `app.py` → Backend Flask (Render.com, gratuit)

---

## ÉTAPE 1 — Déployer le backend sur Render.com

1. Créez un compte gratuit sur https://render.com
2. Cliquez **New → Web Service**
3. Connectez votre dépôt GitHub (ou uploadez les fichiers)
4. Configurez :
   - **Name** : `examen-tec` (ou ce que vous voulez)
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app`
   - **Plan** : Free
5. Cliquez **Create Web Service**
6. Attendez ~2 minutes → Render vous donne une URL comme :
   **`https://examen-tec.onrender.com`**

---

## ÉTAPE 2 — Mettre l'URL dans les fichiers HTML

Ouvrez `examen.html` et `enseignant.html`, cherchez cette ligne :
```javascript
const API_BASE = 'https://VOTRE-APP.onrender.com';
```
Remplacez par votre vraie URL Render, par exemple :
```javascript
const API_BASE = 'https://examen-tec.onrender.com';
```

---

## ÉTAPE 3 — Publier sur GitHub Pages

1. Créez un dépôt GitHub (public)
2. Uploadez : `examen.html`, `enseignant.html`
3. Allez dans **Settings → Pages → Source → main branch**
4. GitHub vous donne l'URL : `https://VOTRE-USERNAME.github.io/REPO-NAME/`

### Liens à partager :
- **Étudiants** : `https://username.github.io/repo/examen.html`
- **Enseignant** : `https://username.github.io/repo/enseignant.html`

---

## Mot de passe enseignant
Le mot de passe par défaut est : **`Ahlemyouya`**  
Vous pouvez le changer dans `enseignant.html` ligne : `const PASSWORD = '...'`

---

## Notes importantes
- Le backend Render.com gratuit se met en veille après 15 min d'inactivité  
  → Ouvrez la page enseignant 5 min avant l'examen pour le réveiller
- Les données sont en mémoire : elles sont perdues si le serveur redémarre  
  → Exportez le CSV dès la fin de l'examen !
- Pour 800 étudiants simultanés, le plan gratuit Render suffit pour un examen court
