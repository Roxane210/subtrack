"""SubTrack — Lanceur portable.

Démarre le serveur local (FastAPI/uvicorn) puis ouvre automatiquement le
navigateur sur l'interface. Fonctionne en mode développement (python launcher.py)
ou empaqueté avec PyInstaller (SubTrack.exe).

Fermer cette fenêtre (ou Ctrl+C) arrête SubTrack.
"""
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path

PORT_DE_BASE = int(os.environ.get("SUBTRACK_PORT", "8085"))


def _port_libre(depart: int, essais: int = 10) -> int:
    """Retourne le premier port disponible à partir de `depart`."""
    for p in range(depart, depart + essais):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start


def main() -> None:
    if getattr(sys, "frozen", False):
        # Version empaquetée (PyInstaller) : les données vivent à côté de l'exécutable,
        # donc dans le dossier dézippé par l'utilisateur (portable / clé USB).
        base_dir = Path(sys.executable).resolve().parent
        os.environ["DATA_DIR"] = str(base_dir / "data")
        os.chdir(base_dir)

    port = _port_libre(PORT_DE_BASE)
    url = f"http://127.0.0.1:{port}"
    data_dir = os.environ.get("DATA_DIR", "./data")

    print("=" * 54)
    print("  SubTrack — Gestionnaire d'abonnements (portable)")
    print("=" * 50)
    print(f"  Interface : {url}")
    print(f"  Données   : {Path(data_dir if 'DATA_DIR' in os.environ else './data').resolve()}")
    print("  Le navigateur va s'ouvrir dans quelques secondes.")
    print("  Fermez cette fenêtre pour arrêter SubTrack.")
    print("=" * 50)

    # Import AVANT uvicorn.run : garantit l'initialisation de la base (create_all)
    # et évite les problèmes d'import par chaîne de caractères en mode gelé.
    from app.main import app  # noqa: F401  (initialise models + sqlite)
    import uvicorn

    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass