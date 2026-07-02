# 📄 OCR Project - Évaluation d'Outils OCR Open Source

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7.0.3-green.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Docling](https://img.shields.io/badge/Docling-2.10.0-orange.svg)](https://github.com/DS4SD/docling)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.2-red.svg)](https://github.com/JaidedAI/EasyOCR)
[![TrOCR](https://img.shields.io/badge/TrOCR-Transformers-purple.svg)](https://huggingface.co/docs/transformers/model_doc/trocr)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-brightgreen.svg)](https://fastapi.tiangolo.com/)

Projet d'évaluation et comparaison de plusieurs solutions OCR open source avec : API REST, interface web, scripts de tests et benchmark.

---

## Présentation

Ce projet regroupe plusieurs moteurs OCR et expose une API et une interface web pour tester et comparer leurs résultats :

- PaddleOCR
- Docling
- EasyOCR
- TrOCR

Il fournit également : scripts de test, génération de rapports de benchmark et utilitaires pour détecter la langue et analyser la confiance des sorties.

## Objectifs

- Intégrer et comparer 4 moteurs OCR open source
- Supporter plusieurs formats (images, PDF, TXT, DOCX, XLSX)
- Proposer une API REST et une interface web interactive
- Fournir une suite de tests et un benchmark reproductible

## Prérequis

- Python 3.10+
- Windows (PowerShell ou CMD) — le projet peut fonctionner sur Linux mais les scripts fournis ciblent Windows
- Environnement virtuel Python recommandé
- Connexion Internet pour télécharger les modèles au premier lancement

---

## Installation

```powershell
cd C:\Users\MSI\Desktop\ocr_project
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Si vous rencontrez des conflits de dépendances (erreurs mentionnant `requests`, `urllib3` ou `charset-normalizer`), exécutez :

```powershell
pip install 'requests>=2.28' 'urllib3>=1.26' 'charset-normalizer==2.1.1'
```

Si la conversion PDF (Docling) échoue, installez `PyMuPDF` :

```powershell
pip install pymupdf
```

> ⚠️ Toujours activer l'environnement virtuel avant d'exécuter les tests ou démarrer l'API :
>
> ```powershell
> .\venv\Scripts\activate
> ```

---

## Démarrage rapide (copy/paste)

```powershell
cd C:\Users\MSI\Desktop\ocr_project
.\venv\Scripts\activate

# Lancer le serveur API
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Ouvrir l'interface dans le navigateur
Start-Process "http://localhost:8000"
```

---

## Endpoints principaux

- `GET /` : page web principale
- `GET /docs` : Swagger UI
- `GET /health` : statut de l'API et base de données
- `GET /models` : informations sur les modèles disponibles
- `POST /extract` : extraction OCR (multipart: `file`, `model`)
- `POST /extract-all` : extraction OCR avec tous les modèles (multipart: `file`)
- `POST /translate` : traduction (texte ou fichier)

Exemple `curl` pour extraire avec Docling :

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@test_files/sample_text.txt" \
  -F "model=docling"
```

---

## Interface Web

La page principale charge `api/static/index_multi.html`. Après upload d'un fichier, l'interface appelle `/extract-all` et affiche les résultats de chaque modèle, la langue détectée, et des métriques de confiance.

Fonctionnalités : prévisualisation, comparaison multi-modèles, traduction intégrée, export texte.

---

## Tests et benchmark

Le dépôt contient plusieurs scripts de test et d'orchestration :

- Tests simples par modèle (image / texte)
- Tests multiformat (benchmark par modèle)
- `run_all_multiformat_tests.py` et `run_all_benchmarks.py`

Commandes utiles :

```powershell
# Tests simples images
python test_paddleocr.py
python test_docling.py
python test_easyocr.py
python test_trocr.py

# Tests simples texte
python test_paddleocr_texte.py
python test_docling_texte.py
python test_easyocr_texte.py
python test_trocr_texte.py

# Tests multiformat
python test_paddleocr_multiformat.py
python test_docling_multiformat.py
python test_easyocr_multiformat.py
python test_trocr_multiformat.py

# Orchestration complète
python run_all_multiformat_tests.py
python run_all_benchmarks.py
```

Les résultats sont sauvegardés dans `test_results/` et `benchmark_results.json`.

---

## Notes de dépannage rapides

- `ModuleNotFoundError`: activez l'environnement virtuel

```powershell
.\venv\Scripts\activate
```

- Timeout worker (300s): fichier trop volumineux ou initialisation lente — réduire la résolution ou tester un fichier plus petit.

- `ngrok` hors-line (`ERR_NGROK_3200`): relancez le tunnel avec `ngrok http 8000` et vérifiez l'URL publique.

- `uvicorn --reload` redémarre continuellement : évitez de créer des fichiers temporaires dans le répertoire du projet (le reloader surveille les modifications). Le code a été modifié pour utiliser le répertoire temporaire système.

---

## Changements récents

- `api/worker.py` : correction d'une indentation erronée qui provoquait des plantages.
- `api/worker.py` : initialisation de `PaddleOCR` rendue tolérante à l'argument `show_log` pour compatibilité.
- `api/main.py` : création des fichiers temporaires dans le répertoire temporaire système (évite les redémarrages du reloader).

---

## Structure du projet (résumé)

```
ocr_project/
├── api/
│   ├── main.py
│   ├── worker.py
│   ├── model_matrix.py
│   ├── language_detector.py
│   ├── confidence_analyzer.py
│   ├── database.py
│   └── static/
│       ├── app.js
│       ├── index_multi.html
│       └── index.html
├── test_files/
├── test_results/
├── demo_images/
├── run_all_benchmarks.py
├── run_all_multiformat_tests.py
├── requirements.txt
└── README.md
```

---

## Auteur

Kinza Chaouachi
