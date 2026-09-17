# AGENTS.md — Règles d'orchestration & rôles des modèles (SubTrack)

Projet : **SubTrack** (Gestionnaire d'abonnements - FastAPI / SQLAlchemy / Alpine.js / Tailwind CSS / Docker Synology).

---

## 🏗️ Répartition des rôles (Architecture à 3 modèles)

Pour optimiser le coût, la vitesse et la qualité du code, chaque intervention respecte cette hiérarchie :

| Rôle | Modèle | Utilisation & Responsabilités |
| :--- | :--- | :--- |
| **1. Orchestrateur** | `openrouter/qwen/qwen3.7-flash` *(défaut)* | **Point d'entrée & planification** : dialogue avec l'utilisateur, exploration de l'arborescence, décomposition des étapes, exécution des commandes Git/shell rapides. |
| **2. Développeur Code** | `openrouter/z-ai/glm-5.3-flash` *(sous-agent)* | **Écriture & modification du code** : implémentation des routes FastAPI, modèles SQLAlchemy, scripts Python et tests `pytest`. Déclenché automatiquement via `delegate_task` (`delegation.model`). |
| **3. Finaliseur & Cosmétique** | `openrouter/google/gemini-3.8-flash:floor` | **Revue globale & finition** : analyse du projet en contexte large (1M tokens), polissage UI/CSS (Tailwind/Alpine), cohérence d'ensemble, documentation et validation pré-PR via `/moa` ou alias `smart`. |

---

## ⚙️ Règles de workflow local

1. **Délégation automatique du code** :
   - L'orchestrateur ne modifie pas de logique complexe directement : il confie l'écriture à un sous-agent délégué (propulsé par GLM 5.3 Flash).
2. **Revue de synthèse & cosmétique** :
   - Avant de finaliser une fonctionnalité ou une PR, lancer une passe de contrôle via Gemini 3.8 Flash (`:floor`) pour vérifier la cohérence d'ensemble et soigner l'ergonomie visuelle.
3. **Cycle Git sécurisé** :
   - Travailler sur une branche dédiée (`feature/...` ou `fix/...`).
   - Valider impérativement les tests en local (`pytest tests/`) avant commit.
   - Soumettre une Pull Request sur GitHub pour validation finale par l'utilisateur.
4. **Étanchéité des secrets** :
   - Aucun fichier `.env` ou clé d'API ne doit être indexé par Git.
