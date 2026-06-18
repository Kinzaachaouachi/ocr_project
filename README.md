# 🔍 OCR Project - PaddleOCR & Docling

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7.0.3-green.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Docling](https://img.shields.io/badge/Docling-2.10.0-orange.svg)](https://github.com/DS4SD/docling)

Projet de test et comparaison de deux solutions OCR (Optical Character Recognition) pour extraire du texte à partir d'images et de documents.

## 🎯 Objectif

Comparer les performances et la précision de **PaddleOCR** et **Docling** pour différents types de documents :
- Images avec texte
- Fichiers texte convertis en images
- Documents structurés

## 🚀 Installation Rapide

```powershell
# Cloner le dépôt
git clone https://github.com/Kinzaachaouachi/ocr_project.git
cd ocr_project

# Créer et activer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate.ps1

# Installer les dépendances
pip install paddleocr==2.7.0.3 paddlepaddle==2.6.2 docling numpy==1.26.4 opencv-python==4.6.0.66 pillow
```

## 📝 Tests Disponibles

| Test | Outil | Type | Fichier |
|------|-------|------|---------|
| Test 1 | PaddleOCR | Image | `test_paddleocr.py` |
| Test 2 | PaddleOCR | Texte → Image | `test_06_paddleocr_avec_texte.py` |
| Test 3 | Docling | Image | `test_01_docling_avec_image.py` |
| Test 4 | Docling | Fichier Texte | `test_05_docling_avec_texte.py` |

## 🏃 Exécution

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\activate.ps1

# Exécuter un test
python test_paddleocr.py
```

## 📊 Résultats

### PaddleOCR
- ⚡ **Vitesse** : ~1.8s (init + OCR)
- 🎯 **Précision** : 97.4%
- 📦 **Types** : Images (PNG, JPG)

### Docling
- 🐢 **Vitesse** : ~6s (init + conversion)
- 🎯 **Précision** : 99%+
- 📦 **Types** : PDF, DOCX, Images, TXT

## 📁 Structure

```
ocr_project/
├── test_paddleocr.py                 # Test PaddleOCR + image
├── test_06_paddleocr_avec_texte.py  # Test PaddleOCR + texte
├── test_01_docling_avec_image.py    # Test Docling + image
├── test_05_docling_avec_texte.py    # Test Docling + texte
├── corpus_test/                      # 10 images de test
├── demo_images/                      # Images de démo
└── README_TESTS.md                   # Documentation complète
```

## 📖 Documentation Complète

Pour plus de détails, consultez :
- **[README_TESTS.md](README_TESTS.md)** - Guide complet des tests
- **[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)** - Rapport de benchmark détaillé 📊

## 🔧 Technologies

- **Python** 3.10
- **PaddleOCR** 2.7.0.3
- **PaddlePaddle** 2.6.2
- **Docling** 2.10.0
- **NumPy** 1.26.4
- **OpenCV** 4.6.0.66

## ⚠️ Notes Importantes

- PaddleOCR nécessite **numpy 1.26.4** (incompatible avec numpy 2.x)
- Toujours activer l'environnement virtuel avant d'exécuter les tests
- Les tests créent automatiquement les dossiers nécessaires

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Forker le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Committer vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📧 Contact

- **GitHub** : [@Kinzaachaouachi](https://github.com/Kinzaachaouachi)
- **Projet** : [ocr_project](https://github.com/Kinzaachaouachi/ocr_project)

---

**Créé le** : 18 juin 2026  
**Dernière mise à jour** : 18 juin 2026
