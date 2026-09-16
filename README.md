# 💳 SubTrack - Gestionnaire d'Abonnements Auto-hébergé

**SubTrack** est une application web légère, moderne et indépendante de gestion d'abonnements et de services récurrents. Elle est conçue pour être déployée via **Docker** sur un **NAS Synology** (ou tout serveur Linux) et utilisée comme **Progressive Web App (PWA)** sur PC et smartphone Android / iOS.

---

## 🚀 Fonctionnalités

1. **Tableau de bord synthétique & KPIs** :
   - Coût total mensuel calculé et équivalent annuel.
   - Ventilation par catégorie (Streaming, Cloud, Outils, Jeux, Télécom, Maison, etc.) avec graphique dynamique en camembert.
   - Compteurs d'abonnements actifs, essais gratuits et résiliés.

2. **Calendrier Mensuel Interactif des Prélèvements** :
   - Calendrier dynamique sur un mois avec affichage par défaut du mois courant.
   - Flèches de navigation mensuelle (mois précédent / mois suivant) et bouton retour direct à « Aujourd'hui ».
   - Visualisation de toutes les opérations et facturations prévues dans le mois avec code couleur par catégorie et prix.
   - Clic gauche sur une opération pour ouvrir la fenêtre de modification, et clic droit pour ouvrir le menu contextuel.
   - Compteur d'opérations du mois et total des dépenses prévues pour le mois affiché.

3. **Gestion complète des abonnements (CRUD & Clic Droit v1.3)** :
   - Nom, Montant, Devise (€, $, £, CHF), Fréquence de facturation (mensuel, annuel, trimestriel, semestriel, hebdo).
   - Date du prochain prélèvement, Moyen de paiement, Catégorie, Statut (*Actif*, *Essai gratuit*, *Résilié*).
   - **Menu contextuel (Clic Droit)** :
     - **Option « Renouveler »** (présente dès qu'une opération est échue) : reporte automatiquement l'échéance à la prochaine occurrence en ajoutant la période de récurrence (+1 mois, +1 an, +1 trimestre, etc.).
     - **Option « Modifier »** : modification de tous les paramètres du service.
     - **Option « Résilier »** : conserve l'historique de l'abonnement sans futurs prélèvements.
     - **Option « Supprimer »** : suppression définitive de la base de données.
   - Lien direct de résiliation et notes contextuelles.

4. **Rappels & Alertes visuelles / PWA** :
   - Bannière d'alerte et badges dynamiques pour les abonnements renouvelés dans les **7 prochains jours**.
   - Notifications Web / PWA du navigateur.

5. **Export / Import complet (Sauvegarde & Restauration)** :
   - Export en 1 clic au format **JSON** et **CSV** (compatible Excel / LibreOffice).
   - Import et restauration depuis des fichiers JSON ou CSV.

6. **Interface Responsive & PWA Mobile-First** :
   - Design moderne avec **Tailwind CSS** et **Alpine.js**.
   - Support complet du **Mode Sombre** (Dark Mode).
   - Installable comme une application native via le **Manifest PWA** et le **Service Worker**.

---

## 🛠️ Stack Technique

- **Backend** : Python 3.11, [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/), [Pydantic v2](https://docs.pydantic.dev/).
- **Base de données** : SQLite (persistance dans `/data/subscriptions.db`).
- **Frontend** : Jinja2, Tailwind CSS, Alpine.js, Chart.js, Lucide Icons.
- **Déploiement** : Docker & Docker Compose.

---

## 📦 Déploiement sur Synology NAS (via Container Manager)

### Méthode 1 : Via l'interface Container Manager (Projet Docker Compose)

1. Connectez-vous à DSM sur votre NAS Synology.
2. Ouvrez **File Station** et créez un dossier, par exemple : `/volume1/docker/subtrack`.
3. Copiez tous les fichiers du projet dans ce dossier.
4. Ouvrez **Container Manager** > **Projet** > **Créer**.
5. Nommez le projet `subtrack`, définissez le chemin sur `/volume1/docker/subtrack` et sélectionnez le fichier `docker-compose.yml`.
6. Cliquez sur **Suivant** puis **Terminer** pour lancer la construction et le démarrage.
7. Accédez à l'application depuis votre navigateur : `http://<IP_DU_NAS>:8090`.

---

### Méthode 2 : En ligne de commande (Docker Compose CLI)

```bash
# Clonez ou copiez le dossier sur votre machine/NAS
cd /chemin/vers/Souscriptions

# Lancement en tâche de fond avec build
docker compose up -d --build
```

L'application est immédiatement accessible sur `http://localhost:8090` (ou l'IP locale de votre machine/NAS).

---

## 📱 Installation en tant que PWA sur Android & PC

1. **Sur Android (Chrome / Brave / Edge)** :
   - Ouvrez `http://<IP_DU_NAS>:8000` (ou via votre nom de domaine / reverse proxy HTTPS).
   - Appuyez sur le menu (3 points en haut à droite) et sélectionnez **« Ajouter à l'écran d'accueil »** ou **« Installer l'application »**.
2. **Sur PC (Chrome / Edge)** :
   - Une icône d'installation apparaît dans la barre d'adresse du navigateur.
   - Cliquez sur **Installer SubTrack** pour obtenir une fenêtre d'application autonome.

---

## 📁 Structure des Fichiers

```text
Souscriptions/
├── app/
│   ├── main.py              # Routes FastAPI, Web, API & Export/Import
│   ├── database.py          # Configuration SQLite & SQLAlchemy
│   ├── models.py            # Modèle Subscription
│   ├── schemas.py           # Validation Pydantic
│   ├── crud.py              # Calculs métier et requêtes BDD
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/app.js        # Logique Alpine.js
│   │   ├── js/sw.js         # Service Worker PWA
│   │   ├── icons/           # Icônes Web App
│   │   └── manifest.json    # Manifeste PWA
│   └── templates/
│       ├── base.html        # Layout global
│       └── index.html       # Dashboard, Modales CRUD, Graphique
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```
