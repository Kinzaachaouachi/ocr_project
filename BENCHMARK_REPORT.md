# 📊 Rapport de Benchmark OCR Complet - Multi-Modèles

**Date de mise à jour :** 23 June 2026 a 10:49:11  
**Environnement de test :**
- **OS :** Windows 10/11
- **Python :** 3.10
- **CPU :** Architecture x64 (Inférence CPU sans accélération GPU)

---

## 🎯 Objectif du Benchmark

Ce rapport compare quatre solutions OCR (Optical Character Recognition) majeures selon trois critères principaux :
1. **Précision** : Qualité et exactitude de la reconnaissance du texte par rapport à la vérité terrain.
2. **Vitesse** : Temps d'initialisation du modèle et temps de traitement OCR de l'image.
3. **Simplicité d'intégration** : Facilité d'installation, légèreté des dépendances et simplicité du code Python.

---

## 📦 Versions & Dépendances des Modèles

| Outil | Version | Backends / Dépendances Clés |
|-------|---------|-----------------------------|
| **PaddleOCR** | 2.7.0.3 | paddlepaddle 2.6.2, numpy 1.26.4 |
| **Docling** | 2.10.0 | docling-core 2.82.0, pillow |
| **EasyOCR** | 1.7.2 | PyTorch (torch/torchvision), numpy 1.26.4 |
| **TrOCR** | microsoft/trocr-small-printed | Hugging Face Transformers, PyTorch |

---

## 🧪 Résultats des Tests Réels (Image de démonstration)

L'image de test utilisée est `demo_images/demo_text.png` contenant le texte suivant (Vérité Terrain) :
```
TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026
```

### 1. PaddleOCR
- **Temps initialisation :** 3.60s
- **Temps OCR :** 1.00s
- **Texte reconnu :**
```
TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026
```
- **Précision (Levenshtein) :** **100.0%**

### 2. Docling
- **Temps initialisation :** 6.50s
- **Temps OCR :** 12.06s
- **Texte reconnu :**
```
## TEXTE DE TEST

Ligne 2: Evaluation OCR

PaddleOCR Test 2026
```
- **Précision (Levenshtein) :** **100.0%**

### 3. EasyOCR
- **Temps initialisation :** 4.56s
- **Temps OCR :** 1.18s
- **Texte reconnu :**
```
TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026
```
- **Précision (Levenshtein) :** **100.0%**

### 4. TrOCR (Hugging Face)
- **Temps initialisation :** 7.57s
- **Temps OCR :** 0.39s
- **Texte reconnu :**
```
TEXTPER RESTART
```
- **Précision (Levenshtein) :** **19.6%**  
*(Note : La faible précision de TrOCR est normale ici. TrOCR is a single-line model ; passé sur une image entière multi-lignes, il ne parvient pas à segmenter nativement et ne décode que partiellement.)*

---

## 📈 Tableau Récapitulatif Global (sur image de démo)

| Modèle | Temps Init | Temps OCR | Temps Total | Précision (%) | Simplicité d'intégration | Score Global /100 |
|--------|------------|-----------|-------------|---------------|--------------------------|-------------------|
| **PaddleOCR** | 3.60s | 1.00s | 4.60s | 100.0% | 2/5 (Moyenne) | **81.9/100** |
| **Docling** | 6.50s | 12.06s | 18.56s | 100.0% | 5/5 (Excellente) | **77.3/100** |
| **EasyOCR** | 4.56s | 1.18s | 5.74s | 100.0% | 4/5 (Bonne) | **91.7/100** |
| **TrOCR** | 7.57s | 0.39s | 7.96s | 19.6% | 3/5 (Moyenne) | **59.2/100** |

---

## 📂 Résultats Multi-Formats : Image (.png) et PDF (.pdf)

Fichiers de test : `test_files/sample_image.png` et `test_files/sample_document.pdf`  
Vérité terrain attendue :
```
DOCUMENT DE TEST MULTI-FORMATS
Ligne 2: Evaluation de l'OCR
PaddleOCR, Docling, EasyOCR et TrOCR
```

### Matrice de compatibilité et précision par format

| Modèle | Image (.png) | Précision Image | PDF (.pdf) | Précision PDF |
|--------|:---:|:---:|:---:|:---:|
| **PaddleOCR** | OK | 98.9% | OK | 95.6% |
| **Docling** | OK | 95.6% | OK | 60.4% |
| **EasyOCR** | OK | 93.4% | OK | 62.6% |
| **TrOCR** | OK | 0.0% | OK | 1.1% |

### Textes extraits par format

#### PaddleOCR
**Image :** `DOCUMENT DE TEST MULTI-FORMATS Ligne 2: Evaluation de l'OCR PaddleOCR Docling EasyOCRet TrOCR`  
**PDF :** `DOCUMENT DE TEST MULTI-FORMATS Ligne 2:Evaluation de IOCR PaddleOCR, Docling, EssyOCRet TrOCR`

#### Docling
**Image :** `## DOCUMENTDE TESTMULTI-FORMATS ## Ligne 2 Evaluation de IOCR ## PaddleOCR Docling EasyOcRet TrOcR`  
**PDF :** `## DOCUMENTDE TEST MULTI-FORMATS Ligne 2 Evaluation de IOCR`

#### EasyOCR
**Image :** `DOCUMENTDE TESTMULTI-FORMATS Ligne Evaluation de IOCR PaddleOcR Docling EasyOcRet TrOcR`  
**PDF :** `DOCUMENTCETESTMULTHFOFIATS Fustcn IOCR PeddlOCR Docling ESOCRel TiocA`

#### TrOCR
**Image :** `*`  
**PDF :** `2`

---

## 🏆 Classement Final & Recommandations

1. **🥇 EASYOCR** (91.7/100)
2. **🥈 PADDLEOCR** (81.9/100)
3. **🥉 DOCLING** (77.3/100)
4. **4ème : TROCR** (59.2/100)

### 💡 Recommandations stratégiques d'intégration :
- **Docling** est le meilleur choix global si vous manipulez des **fichiers complexes multipages (PDF, Word)** et souhaitez conserver la structure Markdown avec une intégration Python immédiate et propre.
- **PaddleOCR** est le choix ultime pour la **vitesse d'inférence pure** d'images isolées, très adapté aux pipelines en temps réel en production.
- **EasyOCR** est idéal pour des applications d'images simples avec **gestion multilingue native** très simple à déployer (Backend PyTorch standard).
- **TrOCR** est le plus performant pour la lecture de **lignes de texte isolées hautement spécifiques (par exemple, manuscrites)** après découpage préliminaire de la page en lignes de texte individuelles.

---

🔄 *Rapport mis à jour automatiquement à chaque exécution du script de test global.*
