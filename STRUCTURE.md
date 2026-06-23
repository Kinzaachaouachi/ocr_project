# 📁 Structure du Projet OCR

## 📂 Fichiers Essentiels

### 📊 Rapports et Résultats
- **`benchmark_report.html`** - Rapport HTML interactif moderne de benchmark
- **`BENCHMARK_REPORT.md`** - Rapport de benchmark détaillé (Markdown)
- **`benchmark_results.json`** - Données réelles des tests exécutés au format JSON

### 📖 Documentation
- **`README.md`** - Documentation principale du projet
- **`README_TESTS.md`** - Guide complet d'utilisation des tests
- **`STRUCTURE.md`** - Ce fichier (structure du projet)

### 🧪 Tests
- **`test_paddleocr.py`** - Test PaddleOCR avec image simple
- **`test_06_paddleocr_avec_texte.py`** - Test PaddleOCR avec texte converti en image
- **`test_01_docling_avec_image.py`** - Test Docling avec image
- **`test_05_docling_avec_texte.py`** - Test Docling avec fichier texte
- **`test_easyocr.py`** - Test EasyOCR avec image simple
- **`test_trocr.py`** - Test TrOCR avec image simple (architecture Transformers)

### 🛠️ Scripts Utilitaires
- **`run_all_benchmarks.py`** - Script principal de benchmark (exécute les 4 modèles en isolation, calcule la similarité de Levenshtein et met à jour automatiquement le JSON, le rapport Markdown et le rapport HTML interactif).

### 📁 Dossiers
- **`demo_images/`** - Image de démonstration utilisée dans les tests
  - `demo_text.png` - Image de démo pour Docling, EasyOCR et TrOCR
- **`corpus_test/`** - 10 images de test variées pour les benchmarks
- **`venv/`** - Environnement virtuel Python
- **`.git/`** - Dépôt Git


## 📊 Statistiques du Projet

- **Tests Python** : 6 fichiers (PaddleOCR x2, Docling x2, EasyOCR, TrOCR)
- **Documentation** : 3 fichiers principaux (README, README_TESTS, STRUCTURE)
- **Rapports** : 1 HTML + 1 Markdown + 1 JSON
- **Images de test** : 11 images (1 demo + 10 corpus)
- **Scripts utilitaires** : 1 fichier principal (`run_all_benchmarks.py`)

---

## 🎯 Commandes Utiles

### Exécuter les tests individuels

```bash
# Activer l'environnement virtuel
.\venv\Scripts\activate

# Tests PaddleOCR
python test_paddleocr.py
python test_06_paddleocr_avec_texte.py

# Tests Docling
python test_01_docling_avec_image.py
python test_05_docling_avec_texte.py

# Test EasyOCR
python test_easyocr.py

# Test TrOCR
python test_trocr.py
```

### Exécuter le Benchmark Global (et régénérer les rapports HTML/MD)
```bash
.\venv\Scripts\activate
python run_all_benchmarks.py
```

### Ouvrir le rapport HTML
```bash
start benchmark_report.html
```

---

**Projet maintenu par** : Kinza Achaouachi  
**Dernière mise à jour** : 23 juin 2026