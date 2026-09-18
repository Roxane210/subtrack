#!/usr/bin/env bash
# ============================================================
#  SubTrack — Génération de l'archive ZIP « application portable »
#
#  Usage :
#     ./scripts/build_portable_zip.sh                 # ZIP léger (~150 Ko)
#     ./scripts/build_portable_zip.sh --avec-deps     # ZIP autonome (dépendances embarquées)
#
#  Résultat dans dist/ :
#     SubTrack-v<version>-portable.zip
#     SubTrack-v<version>-portable-avec-deps.zip
#
#  Le script n'efface aucun fichier de travail : la préparation de l'archive
#  se fait dans un dossier temporaire système, et seulement le fichier .zip
#  cible est écrit dans dist/.
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WITH_DEPS=0
case "${1:-}" in
  --avec-deps|--with-deps|-d) WITH_DEPS=1 ;;
  --help|-h) sed -n '2,16p' "$0"; exit 0 ;;
  "") ;;
  *) echo "Option inconnue : $1 (utilisez --avec-deps)" >&2; exit 1 ;;
esac

# --- Version lue depuis le badge du header (source de vérité unique) ---
VERSION="$(grep -oE 'v[0-9]+\.[0-9]+' app/templates/base.html | head -1)"
[ -n "$VERSION" ] || { echo "Version introuvable dans app/templates/base.html" >&2; exit 1; }

SUFFIX=""; [ "$WITH_DEPS" = "1" ] && SUFFIX="-avec-deps"
NAME="SubTrack-${VERSION}-portable${SUFFIX}"
OUT="$ROOT/dist/${NAME}.zip"

mkdir -p "$ROOT/dist"

# Dossier de préparation temporaire (hors dépôt, nettoyé automatiquement)
STAGE_ROOT="$(mktemp -d)"
trap 'rm -rf "$STAGE_ROOT"' EXIT
STAGE="$STAGE_ROOT/$NAME"

echo "→ SubTrack ${VERSION} — construction de dist/${NAME}.zip"
mkdir -p "$STAGE/docs" "$STAGE/data"

# --- Code applicatif + documentation ---
cp -R app "$STAGE/app"
cp requirements.txt README.md CHANGELOG.md "$STAGE/"
if [ -f docs/GUIDE-UTILISATEUR.md ]; then cp docs/GUIDE-UTILISATEUR.md "$STAGE/docs/"; fi

# --- Lanceurs portables ---
cp packaging/portable/run.sh packaging/portable/run.bat packaging/portable/LIRE-MOI.txt "$STAGE/"
printf '' > "$STAGE/data/.gitkeep"

# --- Dépendances embarquées (option) ---
if [ "$WITH_DEPS" = "1" ]; then
  echo "→ Installation des dépendances dans vendor/ (plateforme hôte uniquement)..."
  if command -v uv >/dev/null 2>&1; then
    uv pip install --quiet --target "$STAGE/vendor" -r requirements.txt
  else
    python3 -m pip install --quiet --target "$STAGE/vendor" -r requirements.txt
  fi
  echo "  ⚠ Ce ZIP n'est utilisable que sur une machine de même OS/architecture."
fi

# --- Création du ZIP (bit exécutable préservé pour run.sh, pas de __pycache__) ---
python3 - "$STAGE" "$OUT" <<'PY'
import os, shutil, stat, sys, zipfile

stage, out = sys.argv[1], sys.argv[2]
parent = os.path.dirname(stage)
count = 0

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, dirs, files in os.walk(stage):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")):
                continue
            path = os.path.join(root, name)
            arc = os.path.relpath(path, parent)
            zi = zipfile.ZipInfo.from_file(path, arc)
            mode = os.stat(path).st_mode
            if name in ("run.sh",):
                mode = 0o755
            zi.external_attr = (mode & 0xFFFF) << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(path, "rb") as src, z.open(zi, "w") as dst:
                dst.write(src.read())
            count += 1
print(f"  {count} fichiers archivés")

shutil.rmtree(stage, ignore_errors=True)
PY

SIZE="$(du -h "$OUT" | cut -f1)"
echo "✔ Archive prête : $OUT ($SIZE)"
echo "  Décompresser puis lancer ./run.sh (Linux/macOS) ou run.bat (Windows)."
