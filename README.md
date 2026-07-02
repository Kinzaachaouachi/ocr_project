# OCR Project

Documentation du projet OCR avec extraction multi-modèles, API FastAPI, interface web, benchmarks et comparaisons.

## Présentation

Ce projet rassemble plusieurs moteurs OCR dans une interface unifiée :
- `PaddleOCR`
- `Docling`
- `EasyOCR`
- `TrOCR`

Il inclut :
- une API REST FastAPI pour l'extraction OCR et la traduction,
- une interface web réactive dans `api/static/index_multi.html`,
- des scripts de test et de benchmark,
- une comparaison de résultats avec le benchmark externe `olmOCR-Bench`.

## Prérequis

- Python 3.10+
- Windows (PowerShell ou CMD)
- Environnement virtuel Python recommandé
- Connexion Internet pour télécharger les modèles au premier lancement

## Installation

```powershell
cd C:\Users\MSI\Desktop\ocr_project
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer l'API

```powershell
cd C:\Users\MSI\Desktop\ocr_project
.\venv\Scripts\activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Puis ouvrir :

```text
http://localhost:8000/
```

## Endpoints disponibles

- `GET /` : interface web principale (`index_multi.html`)
- `GET /health` : vérifie le statut de l'API et la connexion à la base de données
- `GET /benchmark` : rapport local du benchmark comparatif des modèles
- `GET /benchmark/olm` : rapport externe `olmOCR-Bench`
- `GET /models` : liste des modèles disponibles et leurs formats supportés
- `GET /history` : historique des extractions stockées
- `GET /history/stats` : statistiques d'usage de l'API
- `POST /extract` : extraction OCR avec un modèle choisi
- `POST /extract-all` : extraction OCR simultanée avec tous les modèles disponibles
- `POST /translate` : traduction de texte extrait ou de fichier

## Modes d'extraction

### Extraction simple

`POST /extract` accepte les fichiers suivants :
- images : `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.webp`
- PDF : `.pdf`
- texte : `.txt`
- Word : `.docx`, `.doc`
- Excel : `.xlsx`, `.xls`

Modèles : `paddleocr`, `docling`, `easyocr`, `trocr`.

### Extraction multi-modèles

`POST /extract-all` exécute l'extraction avec tous les moteurs disponibles et renvoie :
- résultats classés
- langue détectée
- modèles recommandés
- score de qualité et temps de traitement

## Scripts de test et benchmark

### Tests unitaires par modèle

- `python test_paddleocr.py`
- `python test_docling.py`
- `python test_easyocr.py`
- `python test_trocr.py`

### Tests texte

- `python test_paddleocr_texte.py`
- `python test_docling_texte.py`
- `python test_easyocr_texte.py`
- `python test_trocr_texte.py`

### Tests multiformat

- `python test_paddleocr_multiformat.py`
- `python test_docling_multiformat.py`
- `python test_easyocr_multiformat.py`
- `python test_trocr_multiformat.py`

### Orchestration multi-tests

- `python run_all_multiformat_tests.py` : exécute tous les tests multiformat disponibles
- `python run_all_benchmarks.py` : benchmark comparatif local de PaddleOCR, Docling, EasyOCR et TrOCR

### Benchmark olmOCR-Bench

- `python generate_olm_report.py` : génère `olm_benchmark_report.html` à partir de la matrice externe `api/olm_benchmark_matrix.py`
- `GET /benchmark/olm` dans l'API ouvrira ce rapport si le fichier existe

## Structure du projet

```text
ocr_project/
├── api/                          # API REST et logique OCR
│   ├── main.py                   # Application FastAPI
│   ├── worker.py                 # Worker OCR isolé en sous-processus
│   ├── model_matrix.py           # Scores et matrice de modèles internes
│   ├── language_detector.py      # Détection de langue du texte/fichier
│   ├── confidence_analyzer.py    # Calcul de la confiance OCR
│   ├── database.py               # Base SQLite/MySQL et historique
│   ├── olm_benchmark_matrix.py   # Matrice de référence externe olmOCR-Bench
│   └── static/                   # Frontend de l'interface
│       ├── app.js
│       ├── index_multi.html
│       └── index.html
├── corpus_test/                  # Corpus d'images de test
├── demo_images/                  # Images de démonstration
├── test_files/                   # Fichiers texte/doc et PDF de test
├── test_results/                 # Résultats JSON des benchmarks
├── test_paddleocr.py
├── test_paddleocr_texte.py
├── test_paddleocr_multiformat.py
├── test_docling.py
├── test_docling_texte.py
├── test_docling_multiformat.py
├── test_easyocr.py
├── test_easyocr_texte.py
├── test_easyocr_multiformat.py
├── test_trocr.py
├── test_trocr_texte.py
├── test_trocr_multiformat.py
├── test_api.py
├── run_all_benchmarks.py
├── run_all_multiformat_tests.py
├── generate_olm_report.py
├── benchmark_report.html          # Rapport local des 4 modèles
├── olm_benchmark_report.html      # Rapport externe olmOCR-Bench
├── benchmark_results.json
├── BENCHMARK_REPORT.md
├── requirements.txt
└── README.md
```

## Notes importantes

- `api/worker.py` isole chaque moteur OCR dans un sous-processus pour éviter les conflits de bibliothèques (PyTorch vs PaddlePaddle) sur Windows.
- `Docling` supporte davantage de formats (`TXT`, `DOCX`, `XLSX`) que les autres moteurs.
- `TrOCR` est meilleur sur les lignes isolées et peut être lent à initialiser.
- `easyocr` et `paddleocr` sont les meilleurs pour les images multi-langues et les textes courants.

## Dépannage rapide

### Erreur `ModuleNotFoundError`

Vérifier que l'environnement virtuel est activé :

```powershell
.\venv\Scripts\activate
```

### Timeout 300s

Si un worker se termine avec `timeout after 300 seconds`, le fichier est trop lourd ou le modèle met trop de temps à initialiser.

- Réduisez la résolution de l'image
- Testez un fichier plus petit
- Relancez après avoir téléchargé les modèles

### Rapport olyOCR-Bench

Pour générer le rapport externe `olmOCR-Bench` :

```powershell
python generate_olm_report.py
```

Puis ouvrez :

```text
http://localhost:8000/benchmark/olm
```

## Auteur

Kinza Chaouachi
