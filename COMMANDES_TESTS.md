# Commandes de Tests - Projet OCR

**Auteur** : Kinza Achaouachi  
**Projet** : Évaluation d'outils OCR open source  
**Note** : Pour tous les détails, consultez le [README.md](README.md)

---

## 🔧 Installation et Activation

```powershell
# Installation (première fois seulement)
git clone https://github.com/Kinzaachaouachi/ocr_project.git
cd ocr_project
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Activation (à chaque session)
cd c:\Users\MSI\Desktop\ocr_project
.\venv\Scripts\activate
```

---

## 📦 Tests Individuels (5-30 secondes chacun)

```powershell
python test_paddleocr.py
python test_06_paddleocr_avec_texte.py
python test_01_docling_avec_image.py
python test_05_docling_avec_texte.py
python test_easyocr.py
python test_trocr.py
```

---

## 🏆 Benchmarks Comparatifs

```powershell
# Benchmark principal (4 modèles)
python run_all_benchmarks.py

# Tests multi-formats : Image / PDF / TXT
python test_all_file_types.py

# Tests par modèle/format spécifique
python test_all_file_types.py --run-model paddleocr --file-type image
python test_all_file_types.py --run-model docling --file-type pdf
python test_all_file_types.py --run-model easyocr --file-type image
python test_all_file_types.py --run-model trocr --file-type image
```

---

## 📊 Tests Multiformat Complets

```powershell
# Tests individuels par modèle
python test_paddleocr_multiformat.py
python test_docling_multiformat.py
python test_easyocr_multiformat.py
python test_trocr_multiformat.py

# Lancer TOUS les tests multiformat automatiquement
python run_all_multiformat_tests.py
```

---

## 🌐 Tests API REST

```powershell
# Terminal 1: Démarrer le serveur
.\venv\Scripts\activate
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Tests API (dans un autre terminal)
.\venv\Scripts\activate
python test_api.py

# Ouvrir documentation Swagger (dans un navigateur)
Start-Process "http://localhost:8000/docs"

# Accéder à l'interface web
Start-Process "http://localhost:8000"
```

---

## 🎯 Scénarios Recommandés

### Validation Rapide (10 minutes)
```powershell
.\venv\Scripts\activate
python run_all_benchmarks.py
```

### Validation Complète (45 minutes)
```powershell
.\venv\Scripts\activate
python run_all_benchmarks.py
python test_all_file_types.py
python run_all_multiformat_tests.py
```

### Tests par Modèle Individuel
```powershell
# PaddleOCR
python test_paddleocr.py && python test_06_paddleocr_avec_texte.py && python test_paddleocr_multiformat.py

# Docling  
python test_01_docling_avec_image.py && python test_05_docling_avec_texte.py && python test_docling_multiformat.py

# EasyOCR
python test_easyocr.py && python test_easyocr_multiformat.py

# TrOCR
python test_trocr.py && python test_trocr_multiformat.py
```

---

## 🔍 Résolution Problèmes Courants

```powershell
# Erreur ModuleNotFoundError
.\venv\Scripts\activate

# Erreur numpy incompatible 
pip install numpy==1.26.4

# Réinitialiser les dépendances
pip install -r requirements.txt --force-reinstall
```

---

**Pour plus de détails, consultez [README.md](README.md)**
