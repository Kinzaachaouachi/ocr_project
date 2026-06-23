# 🔍 Guide de Test OCR - PaddleOCR, Docling, EasyOCR & TrOCR

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7.0.3-green.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Docling](https://img.shields.io/badge/Docling-2.10.0-orange.svg)](https://github.com/DS4SD/docling)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.2-red.svg)](https://github.com/JaidedAI/EasyOCR)
[![TrOCR](https://img.shields.io/badge/TrOCR-Transformers-purple.svg)](https://huggingface.co/docs/transformers/model_doc/trocr)

Guide complet des tests de comparaison entre quatre solutions OCR sur plusieurs types de fichiers (Image, PDF, TXT).

---

## 📁 Structure du Projet

```
ocr_project/
├── venv/                              # Environnement virtuel Python
├── demo_images/                       # Image de démo (benchmark principal)
├── test_files/                        # Fichiers générés par les tests multi-formats
│   ├── sample_image.png               #   → Image PNG de test
│   ├── sample_document.pdf            #   → PDF de test (converti depuis l'image)
│   └── sample_text.txt                #   → Fichier texte brut de test
├── corpus_test/                       # 10 images de test supplémentaires
│
├── test_paddleocr.py                  # Test PaddleOCR avec image simple
├── test_06_paddleocr_avec_texte.py    # Test PaddleOCR avec texte converti en image
├── test_01_docling_avec_image.py      # Test Docling avec image
├── test_05_docling_avec_texte.py      # Test Docling avec fichier texte
├── test_easyocr.py                    # Test EasyOCR avec image simple
├── test_trocr.py                      # Test TrOCR avec image simple
├── run_all_benchmarks.py              # Benchmark global (image + PDF, 4 modèles)
├── test_all_file_types.py             # Tests multi-formats (image / pdf / txt)
│
├── benchmark_results.json             # Résultats JSON (mis à jour automatiquement)
├── BENCHMARK_REPORT.md                # Rapport Markdown complet avec résultats Image + PDF
└── benchmark_report.html              # Rapport HTML interactif avec graphiques Chart.js
```

---

## 🚀 Installation et Configuration

### **Prérequis**
- Python 3.10
- Windows (PowerShell)
- Connexion Internet (téléchargement des modèles au 1er lancement)

### **Installation**

```powershell
# 1. Cloner le dépôt
git clone https://github.com/Kinzaachaouachi/ocr_project.git
cd ocr_project

# 2. Créer l'environnement virtuel
python -m venv venv

# 3. Activer l'environnement virtuel
.\venv\Scripts\activate

# 4. Installer les dépendances
pip install paddleocr==2.7.0.3 paddlepaddle==2.6.2 docling numpy==1.26.4 opencv-python==4.6.0.66 pillow docling-core easyocr transformers torch torchvision pymupdf img2pdf
```

---

## 🚀 Commandes de Test

### ⚠️ Toujours activer l'environnement virtuel d'abord !

```powershell
.\venv\Scripts\activate
```

---

## 📝 Tests Individuels par Modèle

### **TEST 1 — PaddleOCR avec Image**
**Fichier :** `test_paddleocr.py`  
**Description :** Crée une image avec du texte et la traite avec PaddleOCR.
```powershell
python test_paddleocr.py
```

---

### **TEST 2 — PaddleOCR avec Texte converti**
**Fichier :** `test_06_paddleocr_avec_texte.py`  
**Description :** Convertit du texte en image PNG puis applique PaddleOCR.
```powershell
python test_06_paddleocr_avec_texte.py
```

---

### **TEST 3 — Docling avec Image**
**Fichier :** `test_01_docling_avec_image.py`  
**Description :** Traite une image avec Docling et exporte en Markdown.
```powershell
python test_01_docling_avec_image.py
```

---

### **TEST 4 — Docling avec Fichier Texte**
**Fichier :** `test_05_docling_avec_texte.py`  
**Description :** Crée un fichier `.txt` et le traite avec Docling.
```powershell
python test_05_docling_avec_texte.py
```

---

### **TEST 5 — EasyOCR avec Image**
**Fichier :** `test_easyocr.py`  
**Description :** Traite `demo_images/demo_text.png` avec EasyOCR (français + anglais).
```powershell
python test_easyocr.py
```
**Résultat attendu :**
- Lignes de texte détectées avec score de confiance
- Confiance moyenne affichée
- Temps d'exécution ~1s

---

### **TEST 6 — TrOCR avec Image**
**Fichier :** `test_trocr.py`  
**Description :** Traite une image avec le modèle `microsoft/trocr-small-printed`.
```powershell
python test_trocr.py
```
**Résultat attendu :**
- Modèle chargé (téléchargement ~246MB au 1er lancement)
- Inférence rapide sur une ligne de texte
- ⚠️ Résultats faibles sur images multi-lignes (comportement normal)

---

## 🎯 Scripts de Benchmark

### Option A — Benchmark Global (Recommandé)

Lance les **4 modèles sur image de démo** + **tests Image vs PDF** pour chaque modèle.  
Génère automatiquement `BENCHMARK_REPORT.md` et `benchmark_report.html` :

```powershell
python run_all_benchmarks.py
```

**Ce que fait ce script :**
1. Exécute chaque modèle dans un **sous-processus Python isolé** (évite les conflits `shm.dll` PyTorch/PaddlePaddle sur Windows)
2. Mesure les temps d'initialisation et d'inférence OCR
3. Calcule la précision via la **distance de Levenshtein** par rapport à la vérité terrain
4. Affiche un **tableau ASCII** dans la console (prêt pour capture d'écran)
5. Teste chaque modèle sur `test_files/sample_image.png` et `test_files/sample_document.pdf`
6. Met à jour `benchmark_results.json`, `BENCHMARK_REPORT.md` et `benchmark_report.html`

---

### Option B — Tests Multi-Formats (Image / PDF / TXT)

```powershell
# Matrice complète : 4 modèles × 3 formats (12 tests)
python test_all_file_types.py

# Tester un modèle sur un format précis
python test_all_file_types.py --run-model paddleocr --file-type image
python test_all_file_types.py --run-model paddleocr --file-type pdf
python test_all_file_types.py --run-model paddleocr --file-type txt

python test_all_file_types.py --run-model docling   --file-type image
python test_all_file_types.py --run-model docling   --file-type pdf
python test_all_file_types.py --run-model docling   --file-type txt

python test_all_file_types.py --run-model easyocr   --file-type image
python test_all_file_types.py --run-model easyocr   --file-type pdf

python test_all_file_types.py --run-model trocr     --file-type image
python test_all_file_types.py --run-model trocr     --file-type pdf
```

**Modèles disponibles :** `paddleocr` | `docling` | `easyocr` | `trocr`  
**Formats disponibles :** `image` | `pdf` | `txt`

---

## 📊 Résultats Réels des Tests (23 juin 2026)

### Benchmark sur image de démo (`demo_images/demo_text.png`)

| Modèle | Init | Temps OCR | Temps Total | Précision | Simplicité |
|--------|------|-----------|-------------|-----------|------------|
| **PaddleOCR** | 3.60s | 1.00s | 4.60s | **100.0%** | 2/5 |
| **Docling** | 6.50s | 12.06s | 18.56s | **100.0%** | 5/5 |
| **EasyOCR** | 4.56s | 1.18s | 5.74s | **100.0%** | 4/5 |
| **TrOCR** | 7.57s | 0.39s | 7.96s | 19.6% | 3/5 |

### Tests Multi-Formats : Image vs PDF

Vérité terrain : `DOCUMENT DE TEST MULTI-FORMATS / Ligne 2: Evaluation de l'OCR / PaddleOCR, Docling, EasyOCR et TrOCR`

| Modèle | Image (.png) | Précision Image | PDF (.pdf) | Précision PDF | TXT (.txt) |
|--------|:---:|:---:|:---:|:---:|:---:|
| **PaddleOCR** | ✅ | **98.9%** | ✅ | **95.6%** | ❌ Non supporté |
| **Docling** | ✅ | **95.6%** | ✅ | **60.4%** | ✅ Natif |
| **EasyOCR** | ✅ | **93.4%** | ✅ | **62.6%** | ❌ Non supporté |
| **TrOCR** | ✅ | 0.0% | ✅ | 1.1% | ❌ Non supporté |

**Observations :**
- **PaddleOCR** est le plus stable et précis sur les 2 formats
- **Docling** convertit le PDF nativement et ajoute une structure Markdown (d'où la précision apparente réduite)
- **EasyOCR** perd en précision sur PDF (qualité du rendu PyMuPDF)
- **TrOCR** est inadapté aux images multi-lignes sans segmentation ligne par ligne

---

## 🔧 Dépendances Installées

| Package | Version | Usage |
|---------|---------|-------|
| `paddleocr` | 2.7.0.3 | OCR Paddle |
| `paddlepaddle` | 2.6.2 | Backend deep learning Paddle |
| `docling` | 2.10.0 | Analyse documents (PDF, DOCX, TXT, Images) |
| `easyocr` | 1.7.2 | OCR basé PyTorch, multi-langue |
| `transformers` | 5.12.1 | Accès au modèle TrOCR (Hugging Face) |
| `torch` / `torchvision` | 2.12.1+cpu | Backend EasyOCR & TrOCR |
| `numpy` | 1.26.4 | Verrouillé pour compatibilité PaddleOCR |
| `opencv-python` | 4.6.0.66 | Traitement d'images |
| `pillow` | 12.2.0 | Manipulation d'images |
| `pymupdf (fitz)` | — | Conversion PDF → Image pour OCR |
| `img2pdf` | — | Génération des PDF de test |
| `docling-core` | 2.82.0 | Dépendance interne Docling |

---

## ⚠️ Résolution de Problèmes

### `ModuleNotFoundError`
```powershell
.\venv\Scripts\activate
```

### Erreur NumPy / PaddleOCR
Veillez à utiliser `numpy==1.26.4`. NumPy 2.x est incompatible avec PaddleOCR actuel.

### Conflit `shm.dll` (PyTorch + PaddlePaddle)
PyTorch et PaddlePaddle ne peuvent pas coexister dans le même processus Python sur Windows.  
**Solution :** le script `run_all_benchmarks.py` utilise des **sous-processus isolés** — ne jamais importer les deux dans le même script.

### TrOCR donne de mauvais résultats
C'est normal sur des images multi-lignes. TrOCR lit **une ligne de texte à la fois**. Pour l'utiliser correctement, segmentez l'image en lignes individuelles (CRAFT, YOLO) avant inférence.

### Lenteur au 1er lancement
- PaddleOCR : télécharge les modèles de détection (~10MB)
- EasyOCR : télécharge CRAFT + modèle de reconnaissance (~100MB)
- TrOCR : télécharge `microsoft/trocr-small-printed` (~246MB)
Après le 1er lancement, les modèles sont mis en cache localement.

---

## 📄 Documentation

| Fichier | Description |
|---------|-------------|
| **README.md** | Fiche descriptive principale et installation |
| **README_TESTS.md** | Ce fichier — guide complet des tests |
| **BENCHMARK_REPORT.md** | Rapport de benchmark avec résultats Image + PDF |
| **benchmark_report.html** | Rapport interactif HTML avec graphiques |
| **STRUCTURE.md** | Architecture physique complète du projet |

---

**Dernière mise à jour :** 23 juin 2026
