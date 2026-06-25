# OCR Project - Évaluation d'Outils OCR Open Source

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7.0.3-green.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Docling](https://img.shields.io/badge/Docling-2.10.0-orange.svg)](https://github.com/DS4SD/docling)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.2-red.svg)](https://github.com/JaidedAI/EasyOCR)
[![TrOCR](https://img.shields.io/badge/TrOCR-Transformers-purple.svg)](https://huggingface.co/docs/transformers/model_doc/trocr)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/Status-Complete-success.svg)](#-travaux-réalisés)

**Projet de stage** : Comparaison et évaluation de quatre solutions OCR (Optical Character Recognition) open source pour l'extraction automatique de texte depuis des images, PDF et fichiers texte. Inclut une **API REST FastAPI** et une **interface web interactive**.

---

## 📋 Objectif du Stage

Comparer les performances, la précision et la compatibilité de **PaddleOCR**, **Docling**, **EasyOCR** et **TrOCR** sur différents types de documents :
- Images PNG, JPG, BMP, TIFF, WEBP
- Documents PDF
- Fichiers texte TXT

## 🎯 Travaux Réalisés

| Travail demandé | Statut | Fichiers |
|----------------|--------|----------|
| ✅ Installer les quatre outils | Terminé | `requirements.txt` |
| ✅ Tester sur plusieurs types de documents | Terminé | `corpus_test/` (20+ images variées) |
| ✅ Comparer précision, vitesse, simplicité | Terminé | `BENCHMARK_REPORT.md`, `benchmark_report.html` |
| ✅ Développer une API REST d'extraction | Terminé | `api/main.py`, `api/worker.py` |
| ✅ Créer une interface web interactive | Terminé | `api/static/index.html` |
| ✅ Tester tous formats par modèle | Terminé | `test_all_file_types.py` |

**STATUS: 100% COMPLETE** ✅

---

## 🚀 Installation

### Prérequis

- Python 3.10 ou supérieur
- Windows (PowerShell ou CMD)
- Connexion Internet (téléchargement des modèles au premier lancement)

### Étapes d'Installation

```powershell
# 1. Cloner le dépôt
git clone https://github.com/Kinzaachaouachi/ocr_project.git
cd ocr_project

# 2. Créer l'environnement virtuel
python -m venv venv

# 3. Activer l'environnement virtuel
.\venv\Scripts\activate

# 4. Installer les dépendances
pip install -r requirements.txt
```

> ⚠️ **Important** : Toujours activer l'environnement virtuel avant d'exécuter un test :
> ```powershell
> .\venv\Scripts\activate
> ```

---

## 📁 Structure du Projet

```
ocr_project/
├── venv/                              # Environnement virtuel Python
├── api/                               # API REST FastAPI
│   ├── main.py                        # Application FastAPI (endpoints)
│   ├── worker.py                      # Worker OCR en sous-processus isolé
│   └── static/                        # Interface web
│       └── index.html                 # Page web interactive
├── corpus_test/                       # 20+ images de test variées
│   ├── 01_texte_simple.png
│   ├── 02_multiligne.png
│   └── ... (17+ autres images)
├── demo_images/                       # Image de démo principale
│   └── demo_text.png
├── test_files/                        # Fichiers générés par tests (auto-généré)
├── test_results/                      # Résultats JSON des tests (auto-généré)
│
├── test_paddleocr.py                  # Test PaddleOCR simple
├── test_06_paddleocr_avec_texte.py    # Test PaddleOCR avec texte converti
├── test_01_docling_avec_image.py      # Test Docling avec image
├── test_05_docling_avec_texte.py      # Test Docling avec fichier texte
├── test_easyocr.py                    # Test EasyOCR simple
├── test_trocr.py                      # Test TrOCR simple
│
├── test_paddleocr_multiformat.py      # Tests PaddleOCR sur corpus complet
├── test_docling_multiformat.py        # Tests Docling multi-formats
├── test_easyocr_multiformat.py        # Tests EasyOCR multi-formats
├── test_trocr_multiformat.py          # Tests TrOCR sur sélection d'images
│
├── run_all_benchmarks.py              # Benchmark global (4 modèles)
├── run_all_multiformat_tests.py       # Lance tous les tests multiformat
├── test_all_file_types.py             # Tests Image/PDF/TXT par modèle
├── test_api.py                        # Tests automatiques de l'API REST
│
├── benchmark_results.json             # Résultats JSON (auto-généré)
├── BENCHMARK_REPORT.md                # Rapport Markdown complet
├── benchmark_report.html              # Rapport HTML interactif
├── requirements.txt                   # Dépendances Python
└── README.md                          # Ce fichier (documentation complète)
```

---

## 🧪 Guide Complet des Tests

### Catégorie 1 : Tests Unitaires Rapides (5-30 secondes chacun)

Ces tests valident rapidement que chaque modèle OCR fonctionne correctement.

**Test PaddleOCR Simple**
```powershell
python test_paddleocr.py
```
- Crée une image 600×200 avec du texte
- Mesure temps d'initialisation et d'inférence
- Affiche score de confiance par ligne
- ⏱️ Temps estimé : 5-10 secondes

**Test PaddleOCR avec Texte Converti**
```powershell
python test_06_paddleocr_avec_texte.py
```
- Convertit un document texte en image 800×600
- Applique PaddleOCR sur l'image générée
- Affiche statistiques de confiance
- ⏱️ Temps estimé : 5-10 secondes

**Test Docling avec Image**
```powershell
python test_01_docling_avec_image.py
```
- Traite `demo_images/demo_text.png`
- Exporte le résultat en Markdown
- Affiche nombre de blocs et caractères
- ⏱️ Temps estimé : 15-20 secondes

**Test Docling avec Fichier Texte**
```powershell
python test_05_docling_avec_texte.py
```
- Crée un fichier TXT structuré
- Conversion native (pas d'OCR)
- Préserve la structure Markdown
- ⏱️ Temps estimé : <1 seconde

**Test EasyOCR**
```powershell
python test_easyocr.py
```
- Traite `demo_images/demo_text.png`
- Détection français + anglais
- Affiche scores de confiance par ligne
- ⏱️ Temps estimé : 5-15 secondes (CPU)

**Test TrOCR**
```powershell
python test_trocr.py
```
- Utilise modèle `microsoft/trocr-small-printed`
- Télécharge le modèle au premier lancement (~246 MB)
- Optimisé pour lignes de texte isolées
- ⏱️ Temps estimé : 10-30 secondes (1er lancement plus long)

---

### Catégorie 2 : Benchmark Comparatif (Recommandé)

**Benchmark Global - Comparaison des 4 Modèles**
```powershell
python run_all_benchmarks.py
```

Ce que fait ce script :
1. Exécute chaque modèle dans un **sous-processus Python isolé**
2. Teste sur `demo_images/demo_text.png`
3. Calcule la précision via **distance de Levenshtein**
4. Affiche un tableau ASCII comparatif dans la console
5. Teste Image (.png) vs PDF (.pdf) pour chaque modèle
6. Met à jour automatiquement :
   - `benchmark_results.json`
   - `BENCHMARK_REPORT.md`
   - `benchmark_report.html` (graphiques interactifs)

⏱️ **Temps estimé** : 2-4 minutes

**Résultats attendus** :
```
| Modèle      | Init  | OCR   | Total | Précision |
|-------------|-------|-------|-------|-----------|
| PaddleOCR   | 0.9s  | 1.0s  | 1.9s  | 100.0%    |
| Docling     | 0.05s | 13.8s | 13.85s| 100.0%    |
| EasyOCR     | 1.8s  | 3.1s  | 4.9s  | 100.0%    |
| TrOCR       | 21.9s | 0.4s  | 22.3s | 19.6%*    |
```
*TrOCR obtient 19.6% car il lit **une ligne à la fois** — inadapté aux images multi-lignes.

---

**Tests Multi-Formats : Image / PDF / TXT**
```powershell
# Matrice complète : 4 modèles × 3 formats
python test_all_file_types.py

# Tester un modèle sur un format spécifique
python test_all_file_types.py --run-model paddleocr --file-type image
python test_all_file_types.py --run-model docling --file-type pdf
python test_all_file_types.py --run-model easyocr --file-type image
python test_all_file_types.py --run-model trocr --file-type image
```

⏱️ **Temps estimé** : 3-5 minutes pour tous les tests

**Résultats attendus** :
| Modèle | Image | PDF | TXT |
|--------|:---:|:---:|:---:|
| **PaddleOCR** | ✅ | ✅ | ❌ |
| **Docling** | ✅ | ✅ | ✅ |
| **EasyOCR** | ✅ | ✅ | ❌ |
| **TrOCR** | ✅ | ✅ | ❌ |

---

### Catégorie 3 : Tests Multiformat Complets (Corpus Étendu)

**Test PaddleOCR Multiformat**
```powershell
python test_paddleocr_multiformat.py
```
- Teste **toutes** les images du `corpus_test/` (~20 images)
- Classe par difficulté (facile, moyen, difficile, structuré, complexe)
- Génère `test_results/paddleocr_multiformat_results.json`
- ⏱️ Temps estimé : 3-7 minutes

**Test Docling Multiformat**
```powershell
python test_docling_multiformat.py
```
- Teste fichiers texte + sélection d'images
- Excellente performance sur fichiers texte structurés
- Génère `test_results/docling_multiformat_results.json`
- ⏱️ Temps estimé : 2-5 minutes

**Test EasyOCR Multiformat**
```powershell
python test_easyocr_multiformat.py
```
- Teste **toutes** les images du `corpus_test/`
- Multi-langues (français + anglais)
- Génère `test_results/easyocr_multiformat_results.json`
- ⏱️ Temps estimé : 5-10 minutes

**Test TrOCR Multiformat**
```powershell
python test_trocr_multiformat.py
```
- Teste une **sélection** d'images adaptées à TrOCR
- Génère `test_results/trocr_multiformat_results.json`
- ⏱️ Temps estimé : 5-15 minutes

**Lancer TOUS les Tests Multiformat**
```powershell
python run_all_multiformat_tests.py
```
- Exécute les 4 tests multiformat automatiquement
- Génère rapport global
- ⏱️ Temps estimé : 15-35 minutes

---

## 🌐 Interface Web & API REST

### Démarrer l'API avec l'Interface Web

**Étape 1 : Activer l'environnement virtuel**
```powershell
cd c:\Users\MSI\Desktop\ocr_project
.\venv\Scripts\activate
```

**Étape 2 : Démarrer le serveur API**
```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Étape 3 : Accéder à l'interface**
Ouvrez votre navigateur et allez à :
```
http://localhost:8000
```

---

### Utiliser l'Interface Web

#### 1️⃣ Importer un fichier

**Option A : Clic direct**
- Cliquez sur la zone de dépôt (upload area)
- Sélectionnez un fichier depuis votre ordinateur

**Option B : Glisser-déposer (Drag & Drop)**
- Glissez directement un fichier dans la zone de dépôt
- Déposez le fichier

**Formats supportés** :
- **Images** : PNG, JPG, JPEG, BMP, TIFF, WEBP
- **Documents** : PDF
- **Texte** : TXT (Docling seulement)

**Taille maximale** : 50 MB

#### 2️⃣ Sélectionner le modèle OCR

Quatre modèles sont disponibles :

| Modèle | Spécialité | Vitesse | Précision | Recommandé pour |
|--------|-----------|---------|-----------|-----------------|
| **PaddleOCR** | Rapide & Précis | ⚡⚡ Très rapide | 🎯 99% | Images standards |
| **Docling** | Documentaire | 🐢 Lent | 🎯 96% | PDF, documents, TXT |
| **EasyOCR** | Multi-langue | ⚡ Rapide | 🎯 93% | Texte variés |
| **TrOCR** | Transformer | ⚡ Rapide | ⚠️ Variable | Lignes isolées |

#### 3️⃣ Lancer l'extraction

1. Cliquez sur le bouton **"Extraire le texte"** (activé après sélection d'un fichier)
2. Patientez pendant le traitement (spinner d'attente s'affiche)
3. Les résultats s'affichent automatiquement dans la section droite

#### 4️⃣ Consulter les résultats

**Onglet 1 : Texte Extrait**
- Affiche le texte brut extrait du fichier
- Bouton **"Copier le texte"** pour copier dans le presse-papiers

**Onglet 2 : Statistiques**
Affiche des métriques utiles :
- Nombre total de caractères
- Nombre de mots détectés
- Nombre de lignes
- Nombre de paragraphes

**Onglet 3 : Performance**
Détails temporels :
- Initialisation du modèle
- Extraction OCR
- Temps modèle total
- Temps réel (wall time incluant transferts réseau)

---

### Endpoints API

L'API REST propose les endpoints suivants :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Interface web principale |
| `/health` | GET | Vérification statut API |
| `/models` | GET | Liste des 4 modèles disponibles |
| `/extract` | POST | Extraction OCR (fichier + modèle) |
| `/docs` | GET | Documentation Swagger interactive |
| `/redoc` | GET | Documentation ReDoc alternative |

**Exemple d'utilisation** :

```powershell
# Terminal 1 : Démarrer le serveur
.\venv\Scripts\activate
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 : Tester les endpoints
.\venv\Scripts\activate
python test_api.py
```

**Ouvrir Swagger (documentation interactive)** :
```powershell
Start-Process "http://localhost:8000/docs"
```

---

## 🔍 Différence : Tests Individuels vs Tests Multiformat

### Tests Individuels (5-30 secondes chacun)

**Objectif** : Validation rapide que chaque modèle OCR fonctionne correctement

**Caractéristiques** :
- **1 seule image** par test (généralement `demo_images/demo_text.png`)
- **Test unitaire** : vérifie juste que le modèle s'initialise et traite l'image
- **Temps très court** : 5-30 secondes maximum
- **Résultat simple** : Texte extrait + temps + score de confiance
- **Usage** : Vérifier que l'installation fonctionne

**Exemple** :
```powershell
python test_paddleocr.py  # 1 image, 10 secondes
```

---

### Tests Multiformat Complets (2-15 minutes chacun)

**Objectif** : Évaluation approfondie des performances sur un **corpus étendu**

**Caractéristiques** :
- **~20 images variées** du dossier `corpus_test/`
- **Analyse par catégories** : facile, moyen, difficile, structuré, complexe
- **Statistiques détaillées** : taux de succès par difficulté, temps moyens, scores
- **Fichiers JSON complets** générés dans `test_results/`
- **Temps long** : 2-15 minutes selon le modèle
- **Usage** : Benchmark approfondi pour évaluer les performances réelles

**Exemple** :
```powershell
python test_paddleocr_multiformat.py  # ~20 images, 5 minutes
```

---

### Quand Utiliser Chaque Type ?

| Situation | Tests Recommandés | Temps | Objectif |
|-----------|-------------------|-------|----------|
| **Vérifier l'installation** | Tests Individuels (6 tests) | 2-3 minutes | Validation fonctionnelle |
| **Benchmark rapide** | `run_all_benchmarks.py` | 5 minutes | Comparaison des 4 modèles |
| **Évaluation complète** | Tests Multiformat (M1-M5) | 30 minutes | Performances détaillées |
| **Tests de l'API** | `test_api.py` | 2 minutes | Validation API REST |
| **Démo/Présentation** | Interface web | Temps réel | Usage interactif |

---

## 🎯 Scénarios de Validation Recommandés

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

**PaddleOCR uniquement**
```powershell
python test_paddleocr.py
python test_06_paddleocr_avec_texte.py
python test_paddleocr_multiformat.py
```

**Docling uniquement**
```powershell
python test_01_docling_avec_image.py
python test_05_docling_avec_texte.py
python test_docling_multiformat.py
```

**EasyOCR uniquement**
```powershell
python test_easyocr.py
python test_easyocr_multiformat.py
```

**TrOCR uniquement**
```powershell
python test_trocr.py
python test_trocr_multiformat.py
```

### Tests API
```powershell
# Terminal 1 : Démarrer le serveur
.\venv\Scripts\activate
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 : Tests automatiques
.\venv\Scripts\activate
python test_api.py
```

---

## 📊 Résultats et Rapports

Après exécution des tests, consultez les fichiers générés :

| Fichier | Description |
|---------|-------------|
| **benchmark_results.json** | Données brutes au format JSON |
| **BENCHMARK_REPORT.md** | Rapport détaillé en Markdown |
| **benchmark_report.html** | Rapport HTML interactif avec graphiques |
| **test_results/** | Résultats JSON des tests multiformat |

---

## 🔧 Résolution des Problèmes Courants

### Erreur : ModuleNotFoundError

**Problème** : Module non trouvé lors de l'exécution d'un script

**Solution** : Activer l'environnement virtuel
```powershell
.\venv\Scripts\activate
```

### Erreur NumPy / PaddleOCR

**Problème** : `AttributeError: module 'numpy' has no attribute 'XXX'`

**Solution** : PaddleOCR nécessite numpy 1.26.4
```powershell
pip install numpy==1.26.4
```

### Conflit `shm.dll` (PyTorch + PaddlePaddle)

**Problème** : Erreur lors de l'import simultané de PaddleOCR et TrOCR/EasyOCR

**Explication** : PyTorch et PaddlePaddle ne peuvent pas coexister dans le même processus Python sur Windows.

**Solution** : Le projet utilise des **sous-processus isolés** automatiquement :
- `run_all_benchmarks.py` exécute chaque modèle séparément
- `api/worker.py` isole chaque modèle dans son propre processus
- Ne jamais importer PaddleOCR et TrOCR/EasyOCR dans le même script

### TrOCR donne de mauvais résultats

**Problème** : Précision très faible sur images multi-lignes

**Explication** : C'est **normal**. TrOCR lit **une ligne de texte à la fois**.

**Solution** :
- Utiliser TrOCR uniquement sur lignes isolées
- Pour documents complets : utiliser PaddleOCR/Docling/EasyOCR à la place

### Lenteur au Premier Lancement

**Cause** : Téléchargement des modèles

| Modèle | Taille | Temps (estimation) |
|--------|--------|-------------------|
| PaddleOCR | ~10 MB | 10-30 secondes |
| EasyOCR | ~100 MB | 30-60 secondes |
| TrOCR | ~246 MB | 1-3 minutes |
| Docling | ~20 MB | 20-60 secondes |

Ce n'est pas une erreur, c'est attendu au premier lancement.

### Interface Web ne s'affiche pas

**Vérifiez** :
1. Le serveur fonctionne (http://localhost:8000)
2. Le dossier `api/static/` existe et contient `index.html`
3. Pas de messages d'erreur dans le terminal

### Format non supporté

**Problème** : "Le modèle ne supporte pas ce format"

**Solution** : Vérifier la compatibilité modèle/format

**Formats supportés par modèle** :
- **PaddleOCR** : Images, PDF
- **Docling** : Images, PDF, TXT (natif)
- **EasyOCR** : Images, PDF
- **TrOCR** : Images, PDF

---

## 📚 Documentation Complémentaire

| Fichier | Description |
|---------|-------------|
| **[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)** | Rapport détaillé : 4 modèles, comparaisons, corpus, conclusion |
| **[benchmark_report.html](benchmark_report.html)** | Rapport HTML interactif : graphiques, matrices |

---

## 📈 Exemples de Cas d'Usage

### Cas 1 : Scanner Mobile en Temps Réel
```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='fr', use_gpu=False)
result = ocr.ocr('photo_document.jpg')
# ✅ Rapide (< 2s), précis (~99%)
```

### Cas 2 : Conversion de Documents PDF/DOCX
```python
from docling.document_converter import DocumentConverter
converter = DocumentConverter()
result = converter.convert('contrat.pdf')
markdown = result.document.export_to_markdown()
# ✅ Multi-formats, haute précision (~99%)
```

### Cas 3 : Application Multi-Langues
```python
import easyocr
reader = easyocr.Reader(['fr', 'en', 'de'])
result = reader.readtext('multilingual_doc.png')
# ✅ 80+ langues supportées
```

### Cas 4 : API REST avec Extraction
```bash
curl -X POST "http://127.0.0.1:8000/extract" \
  -F "file=@image.png" \
  -F "model=paddleocr"
```

---

## 👤 Auteur

**Kinza Achaouachi** - [@Kinzaachaouachi](https://github.com/Kinzaachaouachi)

---

## 📅 Historique du Projet

- **18 juin 2026** : Création du projet, tests initiaux PaddleOCR et Docling
- **19 juin 2026** : Ajout EasyOCR et TrOCR, premiers benchmarks
- **20-22 juin 2026** : Développement API REST, tests multi-formats
- **23 juin 2026** : Finalisation benchmarks, documentation complète
- **24 juin 2026** : Correction Unicode (CP1252 Windows compatibility)
- **26 juin 2026** : Interface web, consolidation documentation

---

## 📜 Licence

Ce projet est à usage éducatif et de démonstration dans le cadre d'un stage.

---

**Créé le** : 18 juin 2026  
**Dernière mise à jour** : 26 juin 2026  
**Livrables complétés** : Code source ✅ · Benchmark ✅ · API REST FastAPI ✅ · Interface Web ✅ · Documentation ✅  
**Status** : 100% COMPLETE ✅
