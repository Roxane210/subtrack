# Changelog — SubTrack

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet suit le [Versionnage Sémantique](https://semver.org/lang/fr/).

---

## [1.3.0] — 2026-09-06

### Ajouté
- **Menu contextuel (clic droit)** sur chaque carte d'abonnement dans la liste et le calendrier :
  - Option **Renouveler** : visible uniquement si l'opération est échue (`days_until_renewal < 0`), reporte l'échéance à la prochaine occurrence en ajoutant la période de récurrence (+1 mois, +1 an, +1 trimestre, +1 semestre, +1 semaine).
  - Option **Modifier** : ouvre la modale d'édition.
  - Option **Résilier** : passe le statut à `cancelled`.
  - Option **Supprimer** : suppression définitive avec confirmation.
- **Calendrier mensuel interactif** au-dessus de la section "Répartition par Catégorie" :
  - Affichage du mois courant par défaut.
  - Navigation mois précédent / mois suivant avec flèches.
  - Bouton **Aujourd'hui** pour revenir au mois courant.
  - Badges colorés par catégorie sur les jours concernés.
  - Compteur d'opérations et total des dépenses du mois affiché.
  - Clic gauche → modale de modification. Clic droit → menu contextuel.
- **Endpoint API** `POST /api/subscriptions/{id}/renew` : renouvellement côté serveur.
- Fonction `compute_next_billing_date()` et `renew_subscription()` dans `crud.py`.

### Modifié
- Badge de version dans le header : `v1.2` → `v1.3`.

---

## [1.2.0] — 2026-09-05

### Ajouté
- **Export / Import de données** :
  - `GET /api/export/json` : téléchargement de la base complète au format JSON.
  - `GET /api/export/csv` : téléchargement au format CSV (compatible Excel / LibreOffice).
  - `POST /api/import/json` : import et fusion depuis un fichier JSON.
  - `POST /api/import/csv` : import et fusion depuis un fichier CSV.
  - Modale d'import/export dans le header avec sélecteur de format.
- **Icône Import/Export** dans la barre de navigation principale.

### Modifié
- Badge de version dans le header : `v1.1` → `v1.2`.

---

## [1.1.0] — 2026-09-04

### Ajouté
- **Alertes visuelles** pour les abonnements arrivant à échéance dans les 7 prochains jours (`is_due_soon`).
- Champ `days_until_renewal` calculé dynamiquement dans `SubscriptionOut`.
- Champ `monthly_equivalent` et `yearly_equivalent` pour la normalisation des coûts selon la fréquence.
- **Support Dark Mode** : toggle dans le header, persisté via `localStorage`.
- **Notifications Web / PWA** : demande de permission et affichage de notification lors du rechargement si des abonnements sont proches de l'échéance.
- Compteurs sur le tableau de bord : actifs, essais gratuits, résiliés.

### Modifié
- Badge de version dans le header : `v1.0` → `v1.1`.

---

## [1.0.0] — 2026-09-04

### Initial Release

- **Backend FastAPI** avec SQLAlchemy (SQLite) et Pydantic v2.
- **Modèle `Subscription`** : nom, montant, devise, fréquence de facturation, date de prochain prélèvement, catégorie, moyen de paiement, statut, URL de résiliation, notes.
- **API REST complète** :
  - `GET /api/subscriptions` avec filtres (catégorie, statut, recherche textuelle).
  - `POST /api/subscriptions` : création.
  - `PUT /api/subscriptions/{id}` : modification.
  - `DELETE /api/subscriptions/{id}` : suppression.
  - `GET /api/dashboard` : KPIs agrégés (coût mensuel total, répartition par catégorie).
- **Frontend Alpine.js + Tailwind CSS** :
  - Tableau de bord avec KPIs (coût mensuel, coût annuel, nb abonnements).
  - Graphique camembert (Chart.js) de répartition par catégorie.
  - Liste des abonnements avec filtres et recherche.
  - Modale de création / modification des abonnements.
- **PWA** : Service Worker (`sw.js`), Manifest (`manifest.json`), icônes, installable sur Android et PC.
- **Déploiement Docker** : `Dockerfile` + `docker-compose.yml` avec volume pour la persistance SQLite.
- **Déploiement Firebase** : Cloud Run (`europe-west1`) + Firebase Hosting (`https://projet-voice-bourse.web.app`).
- **Déploiement Synology NAS** : accessible sur `http://192.168.1.118:8090`.

---

## [Unreleased]

### À venir
- Boutons d'export/import rapides directement dans la barre de navigation (sans passer par la modale).
- Notifications push planifiées (Service Worker background sync).
- Statistiques historiques et graphiques d'évolution des dépenses.

---

*Dernière mise à jour : 2026-09-16*
