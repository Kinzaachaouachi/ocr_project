# Guide de Test OCR - PaddleOCR et Docling

## 📁 Structure du Projet

```
ocr_project/
│
├── venv/                      # Environnement virtuel Python
├── corpus_test/              # Images de test (10 documents)
├── demo_images/              # Images de démo
├── test_images/              # Images générées par les tests
│
└── Fichiers de Test:
    ├── test_paddleocr.py                    # Test 1: PaddleOCR avec image
    ├── test_06_paddleocr_avec_texte.py     # Test 2: PaddleOCR avec texte
    ├── test_01_docling_avec_image.py       # Test 3: Docling avec image
    └── test_05_docling_avec_texte.py       # Test 4: Docling avec texte
```

---

## 🚀 Comment Exécuter les Tests

### ⚠️ IMPORTANT: Toujours activer l'environnement virtuel d'abord !

```powershell
cd C:\Users\MSI\Desktop\ocr_project
.\venv\Scripts\activate.ps1
```

---

## 📝 Tests Disponibles

### **TEST 1: PaddleOCR avec Image**

**Fichier:** `test_paddleocr.py`

**Description:** Crée une image avec du texte et la traite avec PaddleOCR

**Commande:**
```powershell
python test_paddleocr.py
```

**Ce que fait le test:**
1. Vérification des dépendances (paddle, opencv, numpy)
2. Initialisation du modèle PaddleOCR
3. Création d'une image de test (`test_images/sample_text.png`)
4. Reconnaissance OCR et affichage des résultats avec scores de confiance

**Résultat attendu:**
- ✓ 3 éléments détectés
- ✓ Confiance moyenne > 95%
- ✓ Temps d'exécution < 2 secondes

---

### **TEST 2: PaddleOCR avec Texte**

**Fichier:** `test_06_paddleocr_avec_texte.py`

**Description:** Convertit du texte en image puis applique PaddleOCR

**Commande:**
```powershell
python test_06_paddleocr_avec_texte.py
```

**Ce que fait le test:**
1. Crée une image (800x600) contenant du texte structuré
2. Sauvegarde dans `test_files/test_text_image.png`
3. Initialise PaddleOCR
4. Reconnaissance OCR et affichage du texte extrait

**Résultat attendu:**
- ✓ Plusieurs lignes de texte détectées
- ✓ Texte reconnu avec structure préservée
- ✓ Statistiques de confiance affichées

---

### **TEST 3: Docling avec Image**

**Fichier:** `test_01_docling_avec_image.py`

**Description:** Traite une image existante avec Docling

**Commande:**
```powershell
python test_01_docling_avec_image.py
```

**Ce que fait le test:**
1. Vérifie l'existence de `demo_images/demo_text.png`
2. Initialise le DocumentConverter de Docling
3. Convertit l'image et extrait le contenu
4. Exporte en Markdown et JSON

**Résultat attendu:**
- ✓ Image trouvée et traitée
- ✓ Contenu extrait en Markdown
- ✓ Statistiques (blocs, caractères, temps) affichées

---

### **TEST 4: Docling avec Texte**

**Fichier:** `test_05_docling_avec_texte.py`

**Description:** Crée un fichier texte et le traite avec Docling

**Commande:**
```powershell
python test_05_docling_avec_texte.py
```

**Ce que fait le test:**
1. Crée un fichier texte structuré (`test_files/test_document.txt`)
2. Initialise le DocumentConverter
3. Convertit le fichier texte
4. Extrait et affiche le contenu en Markdown

**Résultat attendu:**
- ✓ Fichier texte créé
- ✓ Conversion réussie
- ✓ Contenu extrait avec structure préservée

---

## 🎯 Exécuter Tous les Tests en Séquence

```powershell
# 1. Activer l'environnement virtuel
.\venv\Scripts\activate.ps1

# 2. Tests PaddleOCR
python test_paddleocr.py
python test_06_paddleocr_avec_texte.py

# 3. Tests Docling
python test_01_docling_avec_image.py
python test_05_docling_avec_texte.py
```

---

## 🔧 Dépendances Installées

| Package | Version | Usage |
|---------|---------|-------|
| paddleocr | 2.7.0.3 | Reconnaissance OCR |
| paddlepaddle | 2.6.2 | Framework pour PaddleOCR |
| docling | 2.10.0 | Conversion de documents |
| numpy | 1.26.4 | Calculs numériques |
| opencv-python | 4.6.0.66 | Traitement d'images |
| pillow | 12.2.0 | Création d'images |

---

## ⚠️ Résolution de Problèmes

### Problème: "ModuleNotFoundError"
**Solution:** Assurez-vous que l'environnement virtuel est activé:
```powershell
.\venv\Scripts\activate.ps1
```

### Problème: Erreur oneDNN avec PaddleOCR
**Solution:** Les variables d'environnement sont déjà configurées dans les scripts. Si le problème persiste, vérifier que numpy==1.26.4 est installé.

### Problème: "Image non trouvée"
**Solution:** Vérifier que les dossiers `demo_images/` et `corpus_test/` existent.

---

## 📊 Comparaison PaddleOCR vs Docling

| Critère | PaddleOCR | Docling |
|---------|-----------|---------|
| **Vitesse** | ⚡ Rapide (< 2s) | 🐢 Plus lent (> 5s) |
| **Précision** | ✅ Très bonne (> 95%) | ✅ Excellente |
| **Types supportés** | Images (PNG, JPG) | PDF, DOCX, TXT, Images |
| **Stabilité** | ⚠️ Sensible aux dépendances | ✅ Très stable |
| **Facilité d'usage** | ⚠️ Configuration complexe | ✅ Simple |

---

## 📝 Notes

- **PaddleOCR** nécessite numpy 1.26.4 (incompatible avec numpy 2.x)
- **Docling** est plus polyvalent mais plus lent
- Les deux outils fonctionnent bien dans l'environnement virtuel configuré
- Les tests créent automatiquement les dossiers nécessaires (`test_files/`, `test_images/`)

---

**Dernière mise à jour:** 18 juin 2026
