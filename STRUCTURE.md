# 📁 Structure du Projet OCR

## 📂 Fichiers Essentiels

### 📊 Rapports et Résultats
- **`benchmark_report.html`** - Rapport HTML interactif moderne avec images avant/après
- **`BENCHMARK_REPORT.md`** - Rapport de benchmark détaillé (Markdown)
- **`benchmark_results.json`** - Données réelles des tests exécutés

### 📖 Documentation
- **`README.md`** - Documentation principale du projet
- **`README_TESTS.md`** - Guide complet d'utilisation des tests
- **`STRUCTURE.md`** - Ce fichier (structure du projet)

### 🧪 Tests
- **`test_paddleocr.py`** - Test PaddleOCR avec image simple
- **`test_06_paddleocr_avec_texte.py`** - Test PaddleOCR avec texte converti en image
- **`test_01_docling_avec_image.py`** - Test Docling avec image
- **`test_05_docling_avec_texte.py`** - Test Docling avec fichier texte

### 🛠️ Scripts Utilitaires
- **`generate_final_report.py`** - Générateur du rapport HTML moderne (données réelles)
- **`generate_benchmark_html.py`** - Générateur de rapport (réexécute les tests)

### 📁 Dossiers
- **`demo_images/`** - Image de démonstration utilisée dans les tests
  - `demo_text.png` - Image utilisée pour test Docling
- **`corpus_test/`** - 10 images de test variées
  - Images de 01 à 10 (texte simple, multicolore, petit, grand, nombres, etc.)
  - `resultats_docling.json` - Résultats des tests sur le corpus
- **`venv/`** - Environnement virtuel Python
- **`.git/`** - Dépôt Git

## 📋 Fichiers Supprimés (Nettoyage)

### ❌ Rapports en doublon
- `benchmark_report_backup.html`
- `benchmark_report_old.html`
- `benchmark_report.html` (ancien, remplacé par la version moderne)

### ❌ Scripts temporaires
- `update_report.py` - Script temporaire de mise à jour
- `watch_and_update.py` - Script de surveillance (non utilisé)

### ❌ Code non utilisé
- `docling_wrapper.py` - Wrapper alternatif non utilisé

### ❌ Documentation redondante
- `README_HTML_REPORT.md` - Informations déjà dans README.md

### ❌ Dossiers et fichiers temporaires
- `test_images/` - Dossier d'images générées automatiquement
- `test_images/sample_text.png` - Image générée par le script

## 📊 Statistiques du Projet

- **Tests Python** : 4 fichiers
- **Documentation** : 4 fichiers (README, BENCHMARK_REPORT, README_TESTS, STRUCTURE)
- **Rapports** : 1 HTML + 1 Markdown + 1 JSON
- **Images de test** : 11 images (1 demo + 10 corpus)
- **Scripts utilitaires** : 2 fichiers

## 🎯 Commandes Utiles

### Exécuter les tests
```bash
# Activer l'environnement virtuel
.\venv\Scripts\activate

# Tests PaddleOCR
python test_paddleocr.py
python test_06_paddleocr_avec_texte.py

# Tests Docling
python test_01_docling_avec_image.py
python test_05_docling_avec_texte.py
```

### Régénérer le rapport HTML
```bash
.\venv\Scripts\activate
python generate_final_report.py
```

### Ouvrir le rapport HTML
```bash
start benchmark_report.html
```

---

**Projet maintenu par** : Kinza Achaouachi  
**Dernière mise à jour** : 19 juin 2026