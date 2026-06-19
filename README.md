# OCR Project - PaddleOCR & Docling

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7.0.3-green.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Docling](https://img.shields.io/badge/Docling-2.10.0-orange.svg)](https://github.com/DS4SD/docling)

Projet de test et comparaison de deux solutions OCR (Optical Character Recognition) pour extraire du texte à partir d'images et de documents.

## Objectif

Comparer les performances et la précision de **PaddleOCR** et **Docling** pour différents types de documents :
- Images avec texte
- Fichiers texte convertis en images
- Documents structurés

## Installation

```powershell
# Cloner le dépôt
git clone https://github.com/Kinzaachaouachi/ocr_project.git
cd ocr_project

# Créer et activer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate

# Installer les dépendances
pip install paddleocr==2.7.0.3 paddlepaddle==2.6.2 docling numpy==1.26.4 opencv-python==4.6.0.66 pillow docling-core
```

## Tests Disponibles

| Test | Outil | Description | Commande |
|------|-------|-------------|----------|
| Test 1 | Docling | Image | `python test_01_docling_avec_image.py` |
| Test 2 | Docling | Fichier Texte | `python test_05_docling_avec_texte.py` |
| Test 3 | PaddleOCR | Image simple | `python test_paddleocr.py` |
| Test 4 | PaddleOCR | Texte → Image | `python test_06_paddleocr_avec_texte.py` |

## Exécution des Tests

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\activate

# Tests Docling
python test_01_docling_avec_image.py
python test_05_docling_avec_texte.py

# Tests PaddleOCR
python test_paddleocr.py
python test_06_paddleocr_avec_texte.py
```

## Résultats des Tests

### PaddleOCR
- **Vitesse** : ~1.78s (OCR pur, sans premier téléchargement)
- **Précision** : 98.07% (moyenne)
- **Types supportés** : Images (PNG, JPG)

### Docling
- **Vitesse** : ~6.91s (moyenne avec modèles OCR)
- **Précision** : Haute qualité avec structure Markdown
- **Types supportés** : PDF, DOCX, Images, TXT

## Structure du Projet

```
ocr_project/
├── test_paddleocr.py                 # Test PaddleOCR + image simple
├── test_06_paddleocr_avec_texte.py   # Test PaddleOCR + texte converti
├── test_01_docling_avec_image.py     # Test Docling + image
├── test_05_docling_avec_texte.py     # Test Docling + fichier texte
├── docling_wrapper.py                # Wrapper alternatif
├── demo_images/                      # Images de démonstration
├── corpus_test/                      # 10 images de test
├── test_files/                       # Fichiers générés par les tests
├── benchmark_results.json            # Résultats des benchmarks
├── BENCHMARK_REPORT.md               # Rapport détaillé
├── README_TESTS.md                   # Guide complet des tests
└── generate_benchmark_html.py        # Générateur rapport HTML
```

## Documentation

- **[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)** - Rapport de benchmark détaillé avec analyse complète
- **[benchmark_report.html](benchmark_report.html)** - Rapport HTML interactif avec design moderne et images
- **[README_TESTS.md](README_TESTS.md)** - Guide complet des tests

## Technologies

- **Python** 3.10
- **PaddleOCR** 2.7.0.3
- **PaddlePaddle** 2.6.2
- **Docling** 2.10.0
- **NumPy** 1.26.4
- **OpenCV** 4.6.0.66
- **docling-core** 2.82.0

## Notes

- PaddleOCR nécessite **numpy 1.26.4** (incompatible avec numpy 2.x)
- Docling nécessite **docling-core** pour fonctionner correctement
- Toujours activer l'environnement virtuel avant d'exécuter les tests
- Le premier lancement de PaddleOCR télécharge les modèles (~10MB)

## Auteur

**Kinza Achaouachi** - [@Kinzaachaouachi](https://github.com/Kinzaachaouachi)

---

**Créé le** : 18 juin 2026
**Dernière mise à jour** : 18 juin 2026