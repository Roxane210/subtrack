# Roadmap SubTrack

## État actuel (2026-09-17)

- **v1.3** — FastAPI + SQLite + Alpine.js/Tailwind, mono-utilisateur, **sans authentification**
- Instance principale : **Docker sur NAS Synology** (`:8090`), données persistantes via volume
- Instance secondaire : **Cloud Run europe-west1** (déploiement auto via GitHub Actions, repo Artifact Registry `cloud-run`) — sans persistance, à but de test/secours
- PWA prête (manifest + service worker) — installable sur Android/PC
- CI/CD verte : push sur `main` → build → Artifact Registry → Cloud Run

## Étape 1 — Exposition hors NAS (reverse proxy)

- Sous-domaine dédié (ex. `subtrack.<domaine>`) → reverse proxy Synology → `NAS:8090`
- HTTPS obligatoire (Let's Encrypt via DSM) — requis pour PWA hors LAN et TWA
- **Pré-requis sécurité** : ajouter une authentification avant toute exposition publique (au minimum Basic Auth côté proxy, idéalement auth applicative)

## Étape 2 — Multi-utilisateurs

Objectif : chaque utilisateur a **sa propre base de données**.

Approche recommandée :
1. **Authentification** : Firebase Auth (Google sign-in) — cohérent avec l'écosystème existant, SDK côté client + vérification du token côté FastAPI (dépendance `python-jose` ou `firebase-admin`)
2. **Isolation des données** : ajouter `user_id` aux modèles SQLAlchemy + filtrage systématique dans `crud.py` (une seule DB, requêtes filtrées par utilisateur) — plus simple à opérer que N bases SQLite séparées
3. **Migration** : script d'import de la base actuelle vers le schéma `user_id` (l'utilisateur principal récupère ses données existantes)

## Étape 3 — Android

| Option | Effort | Scénario |
|---|---|---|
| PWA (déjà prête) | 0 | Famille : « Ajouter à l'écran d'accueil » |
| TWA (Bubblewrap) | ~1 h | Publication Play Store sans réécrire l'app ; nécessite HTTPS public |
| Native (Capacitor/Flutter) | jours | Seulement si besoin de features natives (push réels, widgets) |

## Décisions actées

- ❌ Pas de persistance Cloud Run (le NAS reste la source de vérité des données)
- ❌ Pas d'auth tant que l'app reste réservée au LAN/usage perso
