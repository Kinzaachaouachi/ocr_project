# OCR Project - PaddleOCR, Docling, EasyOCR & TrOCR

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7.0.3-green.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Docling](https://img.shields.io/badge/Docling-2.10.0-orange.svg)](https://github.com/DS4SD/docling)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.2-red.svg)](https://github.com/JaidedAI/EasyOCR)
[![TrOCR](https://img.shields.io/badge/TrOCR-Transformers-purple.svg)](https://huggingface.co/docs/transformers/model_doc/trocr)

Projet de comparaison de quatre solutions OCR (Optical Character Recognition) sur différents types de fichiers : images PNG, documents PDF et fichiers texte TXT.

## Objectif

Comparer les performances, la précision et la compatibilité de **PaddleOCR**, **Docling**, **EasyOCR** et **TrOCR** sur :
- Images PNG
- Documents PDF
- Fichiers texte TXT

## Installation

```powershell
# Cloner le dépôt
git clone https://github.com/Kinzaachaouachi/ocr_project.git
cd ocr_project

# Créer et activer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate

# Installer les dépendances
pip install paddleocr==2.7.0.3 paddlepaddle==2.6.2 docling numpy==1.26.4 opencv-python==4.6.0.66 pillow docling-core easyocr transformers torch torchvision pymupdf img2pdf
```

## Tests Disponibles

| Test | Outil | Description | Commande |
|------|-------|-------------|----------|
| Test 1 | Docling | Image | `python test_01_docling_avec_image.py` |
| Test 2 | Docling | Fichier Texte | `python test_05_docling_avec_texte.py` |
| Test 3 | PaddleOCR | Image simple | `python test_paddleocr.py` |
| Test 4 | PaddleOCR | Texte → Image | `python test_06_paddleocr_avec_texte.py` |
| Test 5 | EasyOCR | Image simple | `python test_easyocr.py` |
| Test 6 | TrOCR | Image simple | `python test_trocr.py` |
| **Benchmark** | **Tous** | **Comparaison 4 modèles sur image** | **`python run_all_benchmarks.py`** |
| **Multi-formats** | **Tous** | **Tests Image + PDF + TXT** | **`python test_all_file_types.py`** |

## Exécution des Tests

### 1. Activer l'environnement virtuel
```powershell
.\venv\Scripts\activate
```

### 2. Benchmark global (recommandé)
Lance les 4 modèles sur image de démo **ET** teste Image vs PDF pour chaque modèle.
Génère automatiquement `BENCHMARK_REPORT.md` et `benchmark_report.html` :
```powershell
python run_all_benchmarks.py
```

### 3. Test multi-formats uniquement (Image / PDF / TXT)
```powershell
# Tester tous les modèles sur tous les formats (matrice complète)
python test_all_file_types.py

# Tester un modèle sur un format précis
python test_all_file_types.py --run-model paddleocr --file-type image
python test_all_file_types.py --run-model paddleocr --file-type pdf
python test_all_file_types.py --run-model docling   --file-type pdf
python test_all_file_types.py --run-model easyocr   --file-type image
python test_all_file_types.py --run-model trocr     --file-type image

# Modèles disponibles : paddleocr | docling | easyocr | trocr
# Formats disponibles : image | pdf | txt
```

### 4. Tests individuels
```powershell
python test_paddleocr.py
python test_06_paddleocr_avec_texte.py
python test_01_docling_avec_image.py
python test_05_docling_avec_texte.py
python test_easyocr.py
python test_trocr.py
```

---

## Résultats des Benchmarks (23 juin 2026)

### Benchmark sur image de démonstration (`demo_images/demo_text.png`)

| Modèle | Init | Temps OCR | Temps Total | Précision | Simplicité |
|--------|------|-----------|-------------|-----------|------------|
| **PaddleOCR** | 3.60s | 1.00s | 4.60s | **100.0%** | 2/5 |
| **Docling** | 6.50s | 12.06s | 18.56s | **100.0%** | 5/5 |
| **EasyOCR** | 4.56s | 1.18s | 5.74s | **100.0%** | 4/5 |
| **TrOCR** | 7.57s | 0.39s | 7.96s | 19.6% | 3/5 |

> TrOCR obtient 19.6% car il est conçu pour lire **une ligne à la fois** — il échoue sur des images multi-lignes sans segmentation préalable.

### Tests Multi-Formats : Image (.png) vs PDF (.pdf)

Fichiers de test générés dans `test_files/` à partir du contenu :
```
DOCUMENT DE TEST MULTI-FORMATS
Ligne 2: Evaluation de l'OCR
PaddleOCR, Docling, EasyOCR et TrOCR
```

| Modèle | Image (.png) | Précision Image | PDF (.pdf) | Précision PDF | TXT (.txt) |
|--------|:---:|:---:|:---:|:---:|:---:|
| **PaddleOCR** | ✅ | **98.9%** | ✅ | **95.6%** | ❌ Non supporté |
| **Docling** | ✅ | **95.6%** | ✅ | **60.4%** | ✅ Natif |
| **EasyOCR** | ✅ | **93.4%** | ✅ | **62.6%** | ❌ Non supporté |
| **TrOCR** | ✅ | 0.0% | ✅ | 1.1% | ❌ Non supporté |

> PaddleOCR est le plus régulier sur les 2 formats. Les moteurs d'OCR pure (PaddleOCR, EasyOCR, TrOCR) convertissent le PDF en image via **PyMuPDF** avant traitement. Docling traite le PDF nativement mais ajoute un formatage Markdown qui peut réduire la similarité mesurée.

---

## Structure du Projet

```
ocr_project/
├── test_paddleocr.py                 # Test PaddleOCR + image simple
├── test_06_paddleocr_avec_texte.py   # Test PaddleOCR + texte converti
├── test_01_docling_avec_image.py     # Test Docling + image
├── test_05_docling_avec_texte.py     # Test Docling + fichier texte
├── test_easyocr.py                   # Test EasyOCR + image simple
├── test_trocr.py                     # Test TrOCR + image simple
├── run_all_benchmarks.py             # Benchmark global (image + PDF, 4 modèles)
├── test_all_file_types.py            # Tests multi-formats (image/pdf/txt)
├── demo_images/                      # Image de démonstration benchmark
├── test_files/                       # Fichiers générés : sample_image.png, sample_document.pdf, sample_text.txt
├── corpus_test/                      # 10 images de test supplémentaires
├── benchmark_results.json            # Résultats JSON (mis à jour automatiquement)
├── BENCHMARK_REPORT.md               # Rapport Markdown complet
├── benchmark_report.html             # Rapport HTML interactif (graphiques Chart.js)
├── README_TESTS.md                   # Guide détaillé des tests
└── STRUCTURE.md                      # Architecture complète du projet
```

## Documentation

- **[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)** — Rapport de benchmark détaillé avec résultats Image + PDF
- **[benchmark_report.html](benchmark_report.html)** — Rapport HTML interactif : graphiques, matrice de compatibilité, textes extraits
- **[README_TESTS.md](README_TESTS.md)** — Guide complet des tests et commandes

## Technologies

- **Python** 3.10
- **PaddleOCR** 2.7.0.3
- **PaddlePaddle** 2.6.2
- **Docling** 2.10.0
- **EasyOCR** 1.7.2
- **Transformers** 5.12.1 (TrOCR)
- **PyTorch** 2.12.1 (torch/torchvision)
- **NumPy** 1.26.4
- **OpenCV** 4.6.0.66
- **PyMuPDF (fitz)** — conversion PDF → image pour PaddleOCR/EasyOCR/TrOCR
- **img2pdf** — génération des PDF de test
- **docling-core** 2.82.0

## Notes

- PaddleOCR et EasyOCR nécessitent **numpy==1.26.4** (NumPy 2.x provoque des erreurs d'incompatibilité binaire).
- **PyTorch et PaddlePaddle ne peuvent pas coexister dans le même processus Python sur Windows** (`shm.dll`). Le benchmark utilise des **sous-processus isolés** pour éviter ce conflit.
- Docling est le seul modèle prenant en charge nativement les 3 formats (Image, PDF, TXT).
- TrOCR est conçu pour lire **une ligne de texte à la fois** — segmenter l'image en lignes avant de l'utiliser sur des documents multi-lignes.
- Le premier lancement télécharge les modèles : PaddleOCR (~10MB), EasyOCR (~100MB), TrOCR (~246MB).

## Auteur

**Kinza Achaouachi** - [@Kinzaachaouachi](https://github.com/Kinzaachaouachi)

---

**Créé le** : 18 juin 2026  
**Dernière mise à jour** : 23 juin 2026