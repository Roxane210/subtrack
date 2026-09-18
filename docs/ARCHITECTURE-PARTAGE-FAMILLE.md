# Architecture — Partage familial de SubTrack

Objectif : permettre à des membres de la famille (sans accès au NAS) d'utiliser SubTrack
via Chrome (PWA) ou Android, **chacun avec ses propres données persistantes dans le temps**,
et une base démarrant **vide** pour chaque nouvel utilisateur.

---

## 1. Le problème à résoudre

| Contrainte | Conséquence |
|---|---|
| Les membres de la famille n'ont pas accès au NAS | L'app doit être exposée publiquement (HTTPS) |
| Le disque de Cloud Run est **éphémère** | Une base SQLite locale est perdue à chaque redémarrage / instance froide |
| Chaque utilisateur doit avoir **ses** données | Il faut une authentification + une isolation par utilisateur |
| App utilisée par intermittence (quelques fois par semaine) | L'hébergement doit supporter la veille sans réactivation manuelle |

**Conclusion** : la persistance doit sortir du conteneur, et une authentification devient obligatoire
(l'app n'en a aucune aujourd'hui).

---

## 2. Comparatif des hébergements de base de données (vérifié 2026-09)

| Service | Offre gratuite | Points faibles | Verdict |
|---|---|---|---|
| **Neon (Postgres)** | Permanente : 0,5 Go, 100 CU-h/mois, 100 projets, sans CB | Veille après 5 min d'inactivité (mais **réveil automatique** < 1 s) ; 5 Go d'egress/mois | ✅ **Retenu** |
| Supabase (Postgres) | 2 projets, 500 Mo | **Projet mis en pause après ~7 jours d'inactivité, réactivation manuelle** ; pas de backup quotidien | ⚠️ Inadapté (usage intermittent) |
| Fly.io | Plus de free tier (depuis oct. 2024) | ~2 à 5 $/mois minimum | 💰 Payant |
| Render | Free tier permanent (web) | Disques persistants non inclus dans le free | ⚠️ |
| SQLite sur volume GCS monté dans Cloud Run | ~0 € | Pas de verrouillage de fichiers sur FUSE → **risque de corruption** | ❌ Rejeté |

---

## 3. Architectures envisagées

### A. Recommandée — Cloud Run + Postgres Neon + Firebase Auth (0 €)

```
Android / Chrome (PWA ou TWA)
        │  HTTPS
        ▼
  Cloud Run : subtrack            (déploiement auto : push main → GitHub Actions)
        │  SQLAlchemy (couche données inchangée)
        ▼
  Neon Postgres                   (persistant, gratuit, veille auto)
        ▲
        │  vérification du jeton
  Firebase Auth (Google Sign-In)  → user_id en base
```

**Avantages** : coût nul, données persistantes, **aucune réécriture de la couche données**
(SQLAlchemy abstrait le moteur → seul le `DATABASE_URL` change), l'auth Google évite toute
gestion de mots de passe pour la famille, et le déploiement existant reste valable.

**Inconvénients** : première latence ~1 s si la base est en veille ; dépendance à un service tiers.

### B. Tout-Firebase — Firestore au lieu de Postgres

Persistant, gratuit (quota généreux), mais **réécriture complète de la couche données**
(abandon de SQLAlchemy, requêtes et agrégations à refaire, CRUD à adapter).

**Verdict** : plus de travail pour un gain limité (le temps réel et le mode hors-ligne ne sont
pas des besoins ici).

### C. SQLite conservé sur serveur payant (VPS ou Fly.io)

Le code ne change quasiment pas (juste l'auth + `user_id`), mais coûte 2 à 5 €/mois et
demande une maintenance (mises à jour, sauvegardes, certificats).

**Verdict** : solution de repli si l'on veut rester 100 % propriétaire de la donnée.

---

## 4. Travaux à réaliser (architecture A)

### 4.1 Authentification et isolation
1. `models.py` : ajouter `user_id` (String, indexé) à `Subscription` ; clé composite
   `(user_id, key)` pour `Setting`.
2. `main.py` : dépendance `current_user` vérifiant le jeton Firebase (`firebase-admin`),
   injectée dans toutes les routes ; filtrage systématique par `user_id` dans `crud.py`.
3. Frontend : SDK Firebase JS + écran de connexion ; envoi du jeton dans les en-têtes
   `Authorization: Bearer …` de chaque appel `fetch`.
4. **Liste blanche d'émails autorisés** — indispensable pour éviter les inscriptions non désirées.

### 4.2 Bascule de base de données
5. `DATABASE_URL` en variable d'environnement (secret Cloud Run) → Neon.
   **Conserver SQLite en fallback** pour le NAS et les tests locaux (aucune régression).
6. Migration : script d'attribution du `user_id` aux données existantes, ou ré-import du JSON
   via le bouton Import après connexion.

### 4.3 Distribution
7. **PWA** : déjà fonctionnelle (manifest + service worker) → « Ajouter à l'écran d'accueil ».
8. **TWA** (optionnel, plus tard) : `bubblewrap` pour produire un APK/AAB, nécessite un
   fichier `assetlinks.json` servi sur le domaine + HTTPS stable.

### 4.4 Exploitation
9. Sauvegardes : historique Neon de 6 h ; export JSON régulier via le bouton Export.
10. Activer l'authentification **avant** toute exposition publique.

---

## 5. Décisions en attente

- [ ] Choix de l'architecture (A recommandée / B / C)
- [ ] Mode d'authentification (Google Sign-In recommandé / email + mot de passe)
- [ ] Gestion des invitations (liste blanche d'émails)
