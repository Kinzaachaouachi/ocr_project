# -*- coding: utf-8 -*-
r"""
Script de test de l'API OCR REST (FastAPI)
Lance les requetes vers http://localhost:8000

Prerequis : le serveur doit tourner dans un autre terminal :
  venv/Scripts/uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
"""

import json
import time
import urllib.request
import os
import sys

API_URL = "http://localhost:8000"

def test_get(endpoint, description):
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"GET {API_URL}{endpoint}")
    print("-"*70)
    try:
        r = urllib.request.urlopen(f"{API_URL}{endpoint}")
        data = json.loads(r.read())
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("[OK]")
        return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def test_extract(file_path, model, description):
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"POST {API_URL}/extract  |  file={file_path}  |  model={model}")
    print("-"*70)

    if not os.path.exists(file_path):
        print(f"[SKIP] Fichier introuvable : {file_path}")
        return False

    try:
        import http.client
        import mimetypes
        from urllib.parse import urlparse

        # Construire la requete multipart manuellement
        boundary = "----PythonTestBoundary123456"
        filename = os.path.basename(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        with open(file_path, "rb") as f:
            file_data = f.read()

        body = b""
        # Champ "file"
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {mime_type}\r\n\r\n".encode()
        body += file_data
        body += b"\r\n"
        # Champ "model"
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="model"\r\n\r\n'.encode()
        body += model.encode()
        body += b"\r\n"
        body += f"--{boundary}--\r\n".encode()

        parsed = urlparse(f"{API_URL}/extract")
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port)
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }

        t0 = time.time()
        conn.request("POST", "/extract", body=body, headers=headers)
        response = conn.getresponse()
        wall_time = round(time.time() - t0, 2)

        raw = response.read().decode("utf-8")
        status_code = response.status

        try:
            data = json.loads(raw)
            print(f"Status HTTP : {status_code}")
            print(f"Temps total (wall) : {wall_time}s")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception:
            print(f"Status HTTP : {status_code}")
            print(f"Reponse brute : {raw[:500]}")

        conn.close()

        if status_code == 200:
            print("[OK]")
            return True
        else:
            print(f"[ERREUR] Status {status_code}")
            return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


# ─── EXECUTION DES TESTS ──────────────────────────────────────────────────────

print("="*70)
print("       TEST COMPLET DE L'API OCR REST (FastAPI)")
print(f"       Serveur : {API_URL}")
print("="*70)

results = []

# 1. Health Check
results.append(("GET /health", test_get("/health", "Health Check")))

# 2. Liste des modeles
results.append(("GET /models", test_get("/models", "Liste des modeles OCR")))

# 3. Extraction Image avec PaddleOCR
results.append(("PaddleOCR + Image",
    test_extract("demo_images/demo_text.png", "paddleocr", "PaddleOCR sur image demo")))

# 4. Extraction Image avec EasyOCR
results.append(("EasyOCR + Image",
    test_extract("demo_images/demo_text.png", "easyocr", "EasyOCR sur image demo")))

# 5. Extraction Image avec Docling
results.append(("Docling + Image",
    test_extract("demo_images/demo_text.png", "docling", "Docling sur image demo")))

# 6. Extraction Image avec TrOCR
results.append(("TrOCR + Image",
    test_extract("demo_images/demo_text.png", "trocr", "TrOCR sur image demo")))

# 7. Extraction PDF avec PaddleOCR
results.append(("PaddleOCR + PDF",
    test_extract("test_files/sample_document.pdf", "paddleocr", "PaddleOCR sur PDF")))

# 8. Extraction PDF avec Docling
results.append(("Docling + PDF",
    test_extract("test_files/sample_document.pdf", "docling", "Docling sur PDF")))

# 9. Extraction TXT avec Docling
results.append(("Docling + TXT",
    test_extract("test_files/sample_text.txt", "docling", "Docling sur fichier texte")))

# ─── RESUME ──────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("                        RESUME DES TESTS API")
print("="*70)
ok = 0
fail = 0
for name, passed in results:
    status = "[OK]    " if passed else "[ERREUR]"
    print(f"  {status}  {name}")
    if passed:
        ok += 1
    else:
        fail += 1

print("-"*70)
print(f"  Total : {ok} OK / {fail} ERREUR(S) sur {len(results)} tests")
print("="*70)
