# Instructions pour pousser le projet sur GitHub

## ✅ Étapes déjà effectuées :
1. ✓ Dépôt Git initialisé
2. ✓ Fichiers ajoutés au staging
3. ✓ Commit initial créé
4. ✓ Branche `ocr` créée et active

---

## 📝 Prochaines étapes :

### 1️⃣ Créer un nouveau dépôt sur GitHub (si pas encore fait)

Allez sur : https://github.com/Kinzaachaouachi

1. Cliquez sur le bouton vert **"New"** (ou "New repository")
2. Nom du dépôt : `ocr_project` (ou le nom de votre choix)
3. Description : "Projet OCR avec PaddleOCR et Docling - Tests fonctionnels"
4. **Ne cochez PAS** "Initialize with README" (on a déjà les fichiers)
5. Cliquez sur **"Create repository"**

---

### 2️⃣ Lier le dépôt local au dépôt GitHub

Remplacez `NOM_DU_DEPOT` par le nom que vous avez choisi sur GitHub :

```powershell
cd C:\Users\MSI\Desktop\ocr_project
git remote add origin https://github.com/Kinzaachaouachi/NOM_DU_DEPOT.git
```

**Exemple :**
```powershell
git remote add origin https://github.com/Kinzaachaouachi/ocr_project.git
```

---

### 3️⃣ Pousser la branche `ocr` vers GitHub

```powershell
git push -u origin ocr
```

Vous devrez peut-être vous authentifier avec GitHub :
- Nom d'utilisateur : `Kinzaachaouachi`
- Mot de passe : **Personal Access Token** (pas votre mot de passe normal)

**Si vous n'avez pas de token :**
1. Allez sur : https://github.com/settings/tokens
2. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
3. Nom : "OCR Project"
4. Cochez **"repo"** (accès complet aux dépôts)
5. Cliquez sur **"Generate token"**
6. **Copiez le token** (vous ne pourrez plus le voir après !)
7. Utilisez ce token comme mot de passe lors du push

---

### 4️⃣ Vérifier que tout est poussé

Allez sur : `https://github.com/Kinzaachaouachi/NOM_DU_DEPOT`

Vous devriez voir :
- Branche `ocr` active
- 4 fichiers Python de test
- README_TESTS.md
- Les dossiers `corpus_test/` et `demo_images/`

---

## 🔄 Commandes Git utiles pour la suite

### Voir l'état du dépôt
```powershell
git status
```

### Voir les branches
```powershell
git branch
```

### Voir l'historique des commits
```powershell
git log --oneline
```

### Ajouter des modifications futures
```powershell
git add .
git commit -m "Description des changements"
git push origin ocr
```

---

## 📦 Contenu du dépôt (17 fichiers)

```
ocr_project/
│
├── .gitignore                          # Exclusions Git
├── README_TESTS.md                     # Guide des tests
│
├── test_paddleocr.py                   # Test 1: PaddleOCR + image
├── test_06_paddleocr_avec_texte.py    # Test 2: PaddleOCR + texte
├── test_01_docling_avec_image.py      # Test 3: Docling + image
├── test_05_docling_avec_texte.py      # Test 4: Docling + texte
│
├── corpus_test/                        # 10 images de test
│   ├── 01_texte_simple.png
│   ├── 02_texte_multicolore.png
│   ├── 03_texte_petit.png
│   ├── 04_texte_grand.png
│   ├── 05_texte_nombres.png
│   ├── 06_texte_special.png
│   ├── 07_tableau_simple.png
│   ├── 08_texte_italique.png
│   ├── 09_liste_puces.png
│   └── 10_document_complet.png
│
└── demo_images/
    └── demo_text.png                   # Image de démo
```

---

## ⚠️ Note importante

Le dossier `venv/` (environnement virtuel) est **exclu** du dépôt via `.gitignore`.

Pour recréer l'environnement sur une autre machine :
```powershell
python -m venv venv
.\venv\Scripts\activate.ps1
pip install paddleocr==2.7.0.3 paddlepaddle==2.6.2 docling numpy==1.26.4 opencv-python==4.6.0.66 pillow
```

---

**Branche actuelle :** `ocr`  
**Dernière mise à jour :** 18 juin 2026
