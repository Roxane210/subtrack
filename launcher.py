"""SubTrack — Lanceur portable.

Démarre le serveur local (FastAPI/uvicorn), attend qu'il soit prêt, puis
ouvre automatiquement le navigateur sur l'interface. Fonctionne en mode
développement (python launcher.py) ou empaqueté avec PyInstaller (SubTrack.exe).

Fermer cette fenêtre (ou Ctrl+C) arrête SubTrack.
"""
import os
import socket
import sys
import threading
import time
import traceback
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
    return depart


def _ouvrir_navigateur(url: str) -> None:
    """Ouvre l'URL dans le navigateur par défaut (API native sur Windows)."""
    try:
        if sys.platform == "win32" and hasattr(os, "startfile"):
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            webbrowser.open(url)
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass  # l'URL est affichée dans la console de toute façon


def _serveur_pret(port: int, timeout_s: float = 30.0) -> bool:
    """Attend que le serveur réponde sur le port (max `timeout_s`)."""
    limite = time.time() + timeout_s
    while time.time() < limite:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def main() -> None:
    if getattr(sys, "frozen", False):
        # Version empaquetée (PyInstaller) : les données vivent à côté de l'exécutable,
        # donc dans le dossier dézippé par l'utilisateur (portable / clé USB).
        base_dir = Path(sys.executable).resolve().parent
        os.environ["DATA_DIR"] = str(base_dir / "data")
        os.chdir(base_dir)

    data_dir = os.environ.get("DATA_DIR", "./data")
    try:
        Path(data_dir).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    journal = Path(data_dir) / "subtrack.log"

    port = _port_libre(PORT_DE_BASE)
    url = f"http://127.0.0.1:{port}"

    def log(message: str) -> None:
        print(message, flush=True)
        try:
            with open(journal, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {message}\n")
        except OSError:
            pass

    log("=" * 54)
    log("  SubTrack — Gestionnaire d'abonnements (portable)")
    log(f"  Interface : {url}")
    log(f"  Données   : {Path(data_dir).resolve()}")
    log(f"  Journal   : {journal}")
    log("=" * 54)

    try:
        # Import AVANT uvicorn.run : garantit l'initialisation de la base (create_all)
        # et évite les problèmes d'import par chaîne de caractères en mode gelé.
        from app.main import app
        import uvicorn

        serveur = threading.Thread(
            target=lambda: uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning"),
            daemon=True,
        )
        serveur.start()

        if _serveur_pret(port):
            log(f"  Serveur prêt → ouverture du navigateur sur {url}")
            _ouvrir_navigateur(url)
            log("  Si le navigateur ne s'ouvre pas, copiez cette adresse :")
            log(f"    {url}")
            log("  Fermez cette fenêtre pour arrêter SubTrack.")
            while True:
                time.sleep(3600)
        else:
            log("  ERREUR : le serveur n'a pas démarré dans les 30 secondes.")
            log(f"  Consultez le journal : {journal}")

    except Exception:
        log("  ERREUR AU DÉMARRAGE :")
        log(traceback.format_exc())
        try:
            input("Appuyez sur Entrée pour fermer cette fenêtre…")
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass