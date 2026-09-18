# 📘 SubTrack — Guide de l'utilisateur

> **Version documentée : v1.31** — Ce guide s'adresse à une personne qui découvre SubTrack
> pour la première fois. Il explique à quoi sert l'application, ce qu'elle sait faire, et
> comment la lancer en quelques minutes.

---

## 1. SubTrack en une phrase

**SubTrack est un tableau de bord auto-hébergé qui vous dit combien vous coûtent réellement
vos abonnements, quand ils sont prélevés, et vous aide à résilier ce que vous n'utilisez plus.**

Vos données restent chez vous : tout est enregistré dans un unique fichier SQLite
(`data/subscriptions.db`). Aucun compte à créer, aucun service externe, aucune donnée envoyée
sur Internet.

---

## 2. À quoi ça sert concrètement

| Problème courant | Ce que fait SubTrack |
| :--- | :--- |
| « Je ne sais plus combien je paye par mois. » | Total mensuel et annuel calculés automatiquement, quelle que soit la fréquence (hebdo, mensuel, trimestriel, semestriel, annuel). |
| « Ce prélèvement tombe quand ? » | Calendrier mensuel interactif + alerte visuelle pour tout ce qui tombe dans les 7 prochains jours. |
| « J'ai oublié de résilier cet essai gratuit. » | Statut « Essai gratuit » avec compteur dédié sur le tableau de bord, et lien de résiliation enregistré sur chaque abonnement. |
| « Ok j'ai résilié, c'est quand même débité ? » | Bouton « Renouveler » pour reporter l'échéance, ou statut « Résilié » qui conserve l'historique sans futur prélèvement. |
| « Sur quelle carte passe ce paiement ? » | Champ « Moyen de paiement » + filtre dédié, et liste de moyens de paiement gérée dans les Paramètres. |
| « Je veux changer de serveur / sauvegarder. » | Export JSON ou CSV en un clic, réimport pour tout restaurer. |

---

## 3. Ce que l'application sait faire

### 3.1 Tableau de bord
- **KPI** : coût mensuel total, équivalent annuel, nombre d'abonnements actifs.
- **Compteurs** : abonnements actifs, essais gratuits, résiliés.
- **Graphique camembert** de la répartition des dépenses par catégorie
  (Streaming, Cloud, Outils, Jeux, Télécom, Maison, Autre).
- **Bandeau d'alerte** listant les prélèvements prévus dans les 7 prochains jours.

### 3.2 Calendrier mensuel interactif
- Vue du mois courant, navigation mois précédent / suivant, bouton **Aujourd'hui**.
- Chaque échéance apparaît sur sa date, colorée par catégorie, avec son montant.
- **Clic gauche** sur une échéance → ouvre la modification. **Clic droit** → menu contextuel
  (Renouveler / Modifier / Résilier / Supprimer).
- Total des dépenses et nombre d'opérations du mois affiché sous le calendrier.

### 3.3 Gestion des abonnements (créer, modifier, résilier, supprimer)
Chaque abonnement contient : nom, montant, devise (€, $, £, CHF), fréquence de facturation,
date du prochain prélèvement, catégorie, **moyen de paiement**, statut, URL de résiliation, notes.

- **Créer / modifier** via la modale « Nouvel abonnement » (bouton `+`).
- **Clic droit sur une carte** → menu contextuel :
  - **Renouveler** — visible uniquement si l'échéance est passée ; reporte la date
    à la prochaine occurrence en ajoutant la période de récurrence (+1 semaine, +1 mois,
    +1 trimestre, +1 semestre, +1 an).
  - **Modifier** — ouvre la modale d'édition.
  - **Résilier** — passe le statut à « Résilié », conserve l'historique.
  - **Supprimer** — suppression définitive, avec confirmation.

### 3.4 Recherche et filtres
Trois filtres combinables dans la barre de recherche :
1. **Recherche texte** par nom.
2. **Moyen de paiement** — « Tous » ou une valeur précise (voir §3.5).
3. **Catégorie**.

Ils s'appliquent à la fois à la liste et au calendrier.

### 3.5 Paramètres — moyens de paiement (nouveauté v1.31)
Icône **engrenage ⚙️** dans l'en-tête :

- Affiche la liste des moyens de paiement disponibles.
- **Ajouter** un moyen (champ + bouton « Ajouter » ou touche Entrée).
- **Supprimer** un moyen (icône poubelle).
- La liste est **persistée côté serveur** (table `settings`, clé `payment_methods`) : elle est
  partagée entre tous vos appareils et survit au redémarrage.
- Au tout premier lancement, la liste est initialisée automatiquement avec les valeurs par défaut
  (`Carte Bancaire`, `Carte AMEX`, `Prélèvement SEPA`, `PayPal`, `Espèces`) **plus** tous les
  moyens déjà utilisés par vos abonnements existants.
- ⚠️ Supprimer un moyen de paiement de la liste **ne modifie pas** les abonnements qui l'utilisent :
  ceux-ci restent visibles et lisibles.

### 3.6 Moyen de paiement : liste ou saisie libre (non exclusif)
Dans le formulaire d'abonnement, le champ « Moyen de paiement » est une liste déroulante
alimentée par vos Paramètres, avec en tête l'option **« ➕ Autre (saisir)… »** :

- Choix dans la liste → la valeur est enregistrée directement.
- L'option **➕ Autre** → un champ texte apparaît pour saisir une valeur libre.
- À l'enregistrement, si la valeur saisie n'existe pas dans la liste, SubTrack demande :
  *« "X" n'est pas dans la liste des moyens de paiement. L'ajouter à la liste ? »*
  - **Oui** → la valeur est ajoutée à vos Paramètres **et** l'abonnement est enregistré.
  - **Non** → l'abonnement est enregistré quand même avec la valeur libre.
- Une valeur libre reste toujours sélectionnable et filtrable, même absente de la liste.

### 3.7 Export / Import (sauvegarde et migration)
Boutons **Exporter** et **Importer** directement dans l'en-tête :

- `GET /api/export/json` — export complet au format JSON.
- `GET /api/export/csv` — export au format CSV (séparateur `;`, compatible Excel / LibreOffice).
- Import JSON ou CSV : les abonnements sont **fusionnés** avec l'existant.

### 3.8 Application installable (PWA) et mode sombre
- **PWA** : installable sur Android, iOS et PC (Chrome / Edge / Brave) — icône sur l'écran
  d'accueil, plein écran, hors barre d'adresse.
- **Notifications navigateur** : bouton cloche dans l'en-tête ; une notification est affichée
  si des abonnements arrivent à échéance sous 7 jours.
- **Mode sombre** : bascule dans l'en-tête, préférence mémorisée dans le navigateur.
- Interface responsive, pensée mobile d'abord.

---

## 4. Installation

### 4.1 Option A — Application portable (le plus simple, sans Docker)

**Prérequis :** Python 3.11 ou supérieur ([python.org/downloads](https://www.python.org/downloads/)).

1. Récupérez l'archive ZIP portable (voir §5).
2. Décompressez-la où vous voulez.
3. Lancez le lanceur :
   - **Linux / macOS** : `./run.sh`
   - **Windows** : double-clic sur `run.bat`
   - Si `./run.sh` n'est pas exécutable après décompression (certains outils ne
     conservent pas les droits) : `sh run.sh`
4. Ouvrez **http://localhost:8090** dans votre navigateur.

Au premier lancement, un environnement virtuel `.venv` est créé et les dépendances sont
installées automatiquement (comptez ~30 s). Les lancements suivants sont immédiats.
Si l'archive contient un dossier `vendor/`, les dépendances sont déjà embarquées :
le démarrage prend ~2 s et **aucune connexion Internet n'est nécessaire**.

Pour changer le port : `PORT=9000 ./run.sh` (Linux/macOS) ou `set PORT=9000` puis `run.bat` (Windows).

### 4.2 Option B — Docker (recommandé sur NAS Synology ou serveur toujours allumé)

```bash
cd /chemin/vers/subtrack
docker compose up -d --build
```

L'application est alors accessible sur **http://&lt;IP&gt;:8090** depuis n'importe quel appareil
du réseau. Sur Synology, la même chose se fait graphiquement :
**Container Manager → Projet → Créer**, en pointant sur le dossier du projet et le fichier
`docker-compose.yml`. Le volume `./data` garantit la persistance de la base.

### 4.3 Option C — Mode développeur

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --port 8090
```

Tests : `.venv/bin/python -m pytest tests/ -q`

---

## 5. Obtenir le fichier ZIP portable

Le script `scripts/build_portable_zip.sh` fabrique l'archive à partir du dépôt :

```bash
cd /opt/data/projets/subtrack

# ZIP léger (~150 Ko) : dépendances installées au premier lancement (Internet requis une fois)
./scripts/build_portable_zip.sh

# ZIP autonome : dépendances embarquées dans vendor/, utilisable hors ligne
./scripts/build_portable_zip.sh --avec-deps
```

Résultat dans le dossier `dist/` :

```
dist/SubTrack-v1.31-portable.zip
dist/SubTrack-v1.31-portable-avec-deps.zip
```

Contenu de l'archive :

```
SubTrack-v1.31-portable/
├── app/                  # code de l'application (backend + frontend)
├── data/                 # base SQLite créée ici au premier lancement
├── docs/GUIDE-UTILISATEUR.md
├── run.sh                # lanceur Linux / macOS
├── run.bat               # lanceur Windows
├── LIRE-MOI.txt
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

> ⚠️ La variante `--avec-deps` embarque des dépendances **compilées pour la machine qui a
> produit l'archive** (ici : Linux x86_64). Pour un poste Windows, utilisez le ZIP léger
> (les dépendances seront installées au premier lancement), ou lancez le script sur le poste
> Windows lui-même. Le ZIP léger, lui, fonctionne partout.

Le dossier `dist/` est ignoré par Git : aucune archive n'est versionnée dans le dépôt.

---

## 6. Prise en main en 5 minutes

1. Lancez l'application et ouvrez `http://localhost:8090`.
2. Cliquez sur **Paramètres ⚙️** et vérifiez / complétez la liste des moyens de paiement.
3. Cliquez sur le bouton **+ Nouvel abonnement**.
4. Renseignez nom, montant, devise, fréquence, prochain prélèvement, catégorie, moyen de
   paiement et statut. Enregistrez.
5. Recommencez pour vos 3 ou 4 abonnements principaux : le tableau de bord et le calendrier
   se remplissent immédiatement.
6. Si vous voulez importer une liste existante : bouton **Importer** (format JSON ou CSV, une
   ligne par abonnement, mêmes colonnes que l'export).
7. Installez la PWA (« Installer SubTrack » / « Ajouter à l'écran d'accueil ») pour l'avoir
   comme une application native.

---

## 7. Sauvegarde, restauration, réinitialisation

| Action | Comment |
| :--- | :--- |
| **Sauvegarder** | Bouton **Exporter** (JSON ou CSV), ou copiez le fichier `data/subscriptions.db`. |
| **Restaurer** | Bouton **Importer** avec un fichier JSON/CSV, ou remplacez `data/subscriptions.db` par votre sauvegarde (application arrêtée). |
| **Repartir de zéro** | Arrêtez l'application et supprimez `data/subscriptions.db` : elle sera recréée vide au démarrage suivant. |

---

## 8. Questions fréquentes

**Où sont mes données ?**
Dans `data/subscriptions.db`, à côté du lanceur (Docker : dans le volume `/data`). Un seul fichier
contient tout.

**Mes données partent-elles sur Internet ?**
Non. SubTrack fonctionne intégralement en local. Seuls les CDN (Tailwind, Alpine.js, Chart.js,
Lucide) sont chargés depuis Internet pour l'affichage : sans connexion, l'interface reste
fonctionnelle mais son style peut être dégradé.

**Puis-je y accéder depuis mon téléphone ?**
Oui, si l'application tourne sur une machine du même réseau : ouvrez `http://<IP-du-serveur>:8090`
depuis le téléphone, puis « Ajouter à l'écran d'accueil ».

**Que se passe-t-il si je supprime un moyen de paiement utilisé ?**
Rien de grave : les abonnements concernés conservent leur valeur et restent affichés et filtrables.
Le moyen réapparaîtra dans le filtre tant qu'un abonnement l'utilise.

**Un abonnement apparaît en rouge, que faire ?**
Son échéance est passée. Faites un clic droit → **Renouveler** pour la reporter au cycle suivant.

**L'application ne démarre pas.**
Vérifiez que Python ≥ 3.11 est installé (`python3 --version`) et que le port 8090 est libre
(`PORT=9000 ./run.sh` pour en changer).

---

## 9. API REST (usage avancé)

Documentation interactive : **http://localhost:8090/docs** (Swagger UI généré par FastAPI).

| Méthode | Route | Description |
| :--- | :--- | :--- |
| GET | `/api/health` | État du service. |
| GET | `/api/dashboard` | KPI, répartition par catégorie, alertes 7 jours. |
| GET | `/api/subscriptions` | Liste, filtres `category`, `status`, `search`, `payment_method`. |
| POST | `/api/subscriptions` | Création. |
| GET / PUT / DELETE | `/api/subscriptions/{id}` | Lecture / modification / suppression. |
| POST | `/api/subscriptions/{id}/renew` | Reporte l'échéance au cycle suivant. |
| GET | `/api/settings/payment-methods` | Liste des moyens de paiement (auto-initialisée au 1er appel). |
| POST | `/api/settings/payment-methods` | Ajoute un moyen (`{"name": "..."}`), doublons ignorés. |
| DELETE | `/api/settings/payment-methods/{name}` | Retire un moyen de la liste (abonnements inchangés). |
| GET | `/api/export/json` · `/api/export/csv` | Exports téléchargeables. |
| POST | `/api/import/json` · `/api/import/csv` | Imports fusionnants. |

---

*Guide rédigé pour SubTrack v1.31 — voir le `CHANGELOG.md` pour l'historique des versions.*
