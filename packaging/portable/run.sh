#!/usr/bin/env sh
# ============================================================
#  SubTrack — Lanceur portable (Linux / macOS)
#  Usage : ./run.sh   (ou PORT=9000 ./run.sh)
#  Les données sont stockées dans ./data/subscriptions.db
# ============================================================
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8090}"
export DATA_DIR="${DATA_DIR:-./data}"
mkdir -p "$DATA_DIR"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python3}"
else
  echo "ERREUR : python3 introuvable. Installez Python 3.11 ou supérieur." >&2
  exit 1
fi

if [ -d vendor ]; then
  # Dépendances embarquées : aucun accès Internet ni installation requis
  PYTHONPATH="$(pwd)/vendor${PYTHONPATH:+:$PYTHONPATH}"
  export PYTHONPATH
  PY="$PYTHON_BIN"
  echo "→ Dépendances embarquées (dossier vendor/)."
else
  # Environnement virtuel local, créé au premier lancement
  if [ ! -d .venv ]; then
    echo "→ Première exécution : création de l'environnement virtuel..."
    "$PYTHON_BIN" -m venv .venv
    ./.venv/bin/python -m pip install --quiet --upgrade pip || true
    ./.venv/bin/python -m pip install --quiet -r requirements.txt
  fi
  PY="./.venv/bin/python"
fi

echo "→ Démarrage de SubTrack sur http://localhost:${PORT}"
echo "  (Ctrl+C pour arrêter)"
exec "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
