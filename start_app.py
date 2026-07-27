# -*- coding: utf-8 -*-
"""
OCR Intelligence v3.0 -- Application Launcher
Usage: python start_app.py [--host HOST] [--port PORT] [--reload]
"""

import argparse
import subprocess
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Lance le serveur OCR Intelligence")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Adresse d'ecoute (defaut: 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port (defaut: 8000)")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Activer le hot-reload (dev only — interrompt les jobs OCR)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Alias conserve : hot-reload desactive (comportement par defaut)",
    )
    args = parser.parse_args()

    # Hot-reload OFF par defaut : sinon les extractions en arriere-plan sont tuees
    reload = bool(args.reload) and not bool(args.no_reload)

    print("=" * 65)
    print("  OCR Intelligence v3.0.0")
    print("=" * 65)
    print(f"  Interface  : http://{args.host}:{args.port}")
    print(f"  API Docs   : http://{args.host}:{args.port}/docs")
    print(f"  Dashboard  : http://{args.host}:{args.port}/app")
    print(f"  Hot-reload : {'ON' if reload else 'OFF'}")
    if not reload:
        print("  (Jobs OCR stables — utilisez --reload seulement en dev UI)")
    print("=" * 65)
    print()

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nArret du serveur. A bientot !")
    except subprocess.CalledProcessError as e:
        print(f"\nErreur de demarrage : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
