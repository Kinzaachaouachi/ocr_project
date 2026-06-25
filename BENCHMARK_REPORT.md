# 📊 Rapport de Benchmark OCR Complet - Multi-Modèles

    **Date de mise à jour :** 25 June 2026 a 08:24:02  
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
    - **Temps initialisation :** 3.26s
    - **Temps OCR :** 0.98s
    - **Texte reconnu :**
    ```
    TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026
    ```
    - **Précision (Levenshtein) :** **100.0%**

    ### 2. Docling
    - **Temps initialisation :** 7.26s
    - **Temps OCR :** 11.79s
    - **Texte reconnu :**
    ```
    ## TEXTE DE TEST

Ligne 2: Evaluation OCR

PaddleOCR Test 2026
    ```
    - **Précision (Levenshtein) :** **100.0%**

    ### 3. EasyOCR
    - **Temps initialisation :** 5.09s
    - **Temps OCR :** 1.08s
    - **Texte reconnu :**
    ```
    TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026
    ```
    - **Précision (Levenshtein) :** **100.0%**

    ### 4. TrOCR (Hugging Face)
    - **Temps initialisation :** 8.12s
    - **Temps OCR :** 0.44s
    - **Texte reconnu :**
    ```
    TEXTPER RESTART
    ```
    - **Précision (Levenshtein) :** **19.6%**  
    *(Note : TrOCR est un modèle mono-ligne ; sur une image multi-lignes, il ne segmente pas nativement et ne décode qu'une partie du texte.)*

    ---

    ## 📈 Tableau Récapitulatif Global (sur image de démo)

    | Modèle | Temps Init | Temps OCR | Temps Total | Précision (%) | Simplicité d'intégration | Score Global /100 |
    |--------|------------|-----------|-------------|---------------|--------------------------|-------------------|
    | **PaddleOCR** | 3.26s | 0.98s | 4.24s | 100.0% | 2/5 (Moyenne) | **82.1/100** |
    | **Docling** | 7.26s | 11.79s | 19.06s | 100.0% | 5/5 (Excellente) | **77.4/100** |
    | **EasyOCR** | 5.09s | 1.08s | 6.17s | 100.0% | 4/5 (Bonne) | **91.7/100** |
    | **TrOCR** | 8.12s | 0.44s | 8.56s | 19.6% | 3/5 (Moyenne) | **58.9/100** |

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

    ## 📚 Benchmark corpus_test (10 images variées)

    Corpus généré dans `corpus_test/` : texte simple, multiligne, chiffres, accents, majuscules, couleurs, listes, adresses, etc.  
    Vérité terrain : `corpus_test/ground_truth.json`

    | Image | PaddleOCR (précision) | PaddleOCR (OCR) | Docling (précision) | Docling (OCR) |
    |-------|:---:|:---:|:---:|:---:|
    | `01_texte_simple.png` | 15.4% | 1.15s | 15.4% | 15.94s |
| `02_multiligne.png` | 100.0% | 0.88s | 100.0% | 8.28s |
| `03_chiffres.png` | 100.0% | 0.70s | 0.0% | 6.30s |
| `04_accents_francais.png` | 100.0% | 0.75s | 9.5% | 6.88s |
| `05_majuscules.png` | 93.3% | 0.82s | 76.5% | 6.66s |
| `06_phrase_longue.png` | 96.2% | 0.89s | 83.6% | 7.68s |
| `07_texte_bleu.png` | 100.0% | 0.70s | 78.6% | 6.52s |
| `08_liste.png` | 96.4% | 0.86s | 92.6% | 8.09s |
| `09_adresse.png` | 100.0% | 0.82s | 100.0% | 7.77s |
| `10_ligne_unique.png` | 100.0% | 0.72s | 65.0% | 5.92s |

    | **Moyenne corpus** | **90.1%** | **0.83s** | **62.1%** | **8.00s** |

    ---

    ## ⚖️ Comparaison PaddleOCR vs Docling (focus sujet de stage)

    Comparaison directe des **deux outils imposés par le sujet** sur les trois critères demandés.

    | Critère | PaddleOCR | Docling | Gagnant |
    |---------|-----------|---------|---------|
    | **Précision (image démo)** | 100.0% | 100.0% | Égalité |
    | **Précision (PDF)** | 95.6% | 60.4% | PaddleOCR |
    | **Précision moyenne (corpus 10 images)** | 90.1% | 62.1% | PaddleOCR |
    | **Temps OCR (image démo)** | 0.98s | 11.79s | PaddleOCR |
    | **Temps OCR moyen (corpus)** | 0.83s | 8.00s | PaddleOCR |
    | **Simplicité d'intégration** | 2/5 | 5/5 | Docling |
    | **Support PDF natif** | Non (via PyMuPDF) | Oui | Docling |
    | **Support TXT natif** | Non | Oui | Docling |

    **Synthèse :**
    - **PaddleOCR** domine sur la **vitesse** et la **précision OCR pure** sur images isolées.
    - **Docling** domine sur la **simplicité d'intégration**, le **support natif PDF/TXT** et la **structuration Markdown**.

    ---

    ## 🔧 Simplicité d'intégration — Exemples de code

    ### PaddleOCR (~5 lignes utiles)

    ```python
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="fr", use_gpu=False, show_log=False)
    result = ocr.ocr("image.png", cls=True)
    text = "\n".join(line[1][0] for line in result[0])
    print(text)
    ```

    | Aspect | Détail |
    |--------|--------|
    | Lignes de code minimales | ~5 |
    | Dépendances principales | `paddleocr`, `paddlepaddle`, `numpy==1.26.4` |
    | Formats natifs | Images (PNG, JPG…) — PDF via conversion PyMuPDF |
    | Points d'attention | Versions numpy strictes, conflit PyTorch/PaddlePaddle sur Windows |
    | Score simplicité | **2/5** |

    ### Docling (~4 lignes utiles)

    ```python
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert("document.pdf")  # PDF, image ou TXT
    text = result.document.export_to_markdown()
    print(text)
    ```

    | Aspect | Détail |
    |--------|--------|
    | Lignes de code minimales | ~4 |
    | Dépendances principales | `docling`, `docling-core` |
    | Formats natifs | PDF, DOCX, TXT, images |
    | Points d'attention | Temps de traitement plus long sur images simples |
    | Score simplicité | **5/5** |

    ---

    ## 🏆 Classement global (4 modèles — benchmark étendu)

    1. **🥇 EASYOCR** (91.7/100)
    2. **🥈 PADDLEOCR** (82.1/100)
    3. **🥉 DOCLING** (77.4/100)
    4. **4ème : TROCR** (58.9/100)

    ---

    ## ✅ Conclusion du stage

    Ce projet répond aux quatre travaux demandés :

    1. **Installation** — PaddleOCR et Docling installés via `requirements.txt` et environnement virtuel.
    2. **Tests multi-documents** — Images (`demo_images/`, `corpus_test/`), PDF et TXT (`test_files/`).
    3. **Comparaison** — Précision (Levenshtein), vitesse (init + OCR), simplicité (score /5 + exemples de code).
    4. **API REST** — FastAPI (`api/main.py`) avec endpoint `POST /extract`.

    **Recommandation finale (PaddleOCR vs Docling) :**

    | Cas d'usage | Outil recommandé | Justification |
    |-------------|------------------|---------------|
    | Pipeline OCR temps réel sur images | **PaddleOCR** | OCR le plus rapide (0.98s sur démo), haute précision |
    | Extraction de documents PDF/TXT structurés | **Docling** | Support natif multi-formats, export Markdown, intégration la plus simple |
    | API REST polyvalente | **Les deux** | PaddleOCR pour images rapides, Docling pour PDF et fichiers texte |

    Les deux outils sont **complémentaires** : PaddleOCR pour la performance brute sur images, Docling pour l'analyse documentaire intelligente.

    ---

    🔄 *Rapport mis à jour automatiquement à chaque exécution de `python run_all_benchmarks.py`.*
    