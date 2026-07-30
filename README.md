# OCR Intelligence — Plateforme OCR Multi-Modèles

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![Version](https://img.shields.io/badge/Version-3.0.0-purple.svg)](#)

Plateforme web + API REST d’extraction OCR avec **4 moteurs en parallèle** (PaddleOCR, Docling, EasyOCR, TrOCR), authentification sécurisée (vérification email + OTP), dashboard, historique, édition colorée par confiance, jobs asynchrones, notifications, et rapports de benchmark (**PDF uniquement** : Local + OLM Global).

| | |
|---|---|
| **Dépôt** | https://github.com/Kinzaachaouachi/ocr_project |
| **Branche de travail** | `ocr` |
| **Docs API** | http://127.0.0.1:8000/docs · `/redoc` |
| **Santé** | `GET /health` |

---

## Table des matières

1. [Fonctionnalités (inventaire complet)](#1-fonctionnalités-inventaire-complet)
2. [Architecture](#2-architecture)
3. [Prérequis](#3-prérequis)
4. [Installation](#4-installation)
5. [Configuration (.env)](#5-configuration-env)
6. [Démarrage](#6-démarrage)
7. [Pages & navigation](#7-pages--navigation)
8. [Flux d’authentification](#8-flux-dauthentification)
9. [Profil utilisateur](#9-profil-utilisateur)
10. [Extraction OCR](#10-extraction-ocr)
11. [Jobs asynchrones & SharedWorker](#11-jobs-asynchrones--sharedworker)
12. [Persistance extraction (localStorage)](#12-persistance-extraction-localstorage)
13. [Notifications](#13-notifications)
14. [Édition & couleurs de confiance](#14-édition--couleurs-de-confiance)
15. [Traduction](#15-traduction)
16. [Historique](#16-historique)
17. [Dashboard](#17-dashboard)
18. [Rapports benchmark (PDF)](#18-rapports-benchmark-pdf)
19. [API REST (liste complète)](#19-api-rest-liste-complète)
20. [Base de données](#20-base-de-données)
21. [Stack technique](#21-stack-technique)
22. [Scripts & tests](#22-scripts--tests)
23. [Dépannage](#23-dépannage)
24. [Auteur](#24-auteur)

---

## 1. Fonctionnalités

### Authentification & sécurité
- Inscription (`email`, prénom, nom, mot de passe, confirmation, avatar optionnel)
- Compte créé **inactif / non vérifié** jusqu’au clic sur le lien email (token **24 h**)
- Renvoi du lien de vérification
- Après vérification email → envoi automatique d’un **OTP** (ou via login)
- Connexion : si email non vérifié → **403** `EMAIL_NOT_VERIFIED` + renvoi possible
- OTP **6 chiffres**, hashé en base, durée configurable (défaut **10 min**), max **3 essais**, renvoi avec cooldown **60 s**
- JWT après OTP (`Authorization: Bearer …`)
- Mot de passe oublié → lien reset **1 h** → `/reset-password?token=`
- Déconnexion (côté client : suppression du token + clés OCR / notifications)
- Hash mots de passe : **PBKDF2-HMAC-SHA256**

### Profil
- Consultation / mise à jour : prénom, nom, email, changement de mot de passe (actuel + nouveau ≥ 6 caractères avec lettre et chiffre)
- Avatar : PNG / JPG / GIF / WEBP, max **5 Mo** → `/uploads/avatars/…`
- Avatar à l’inscription → `/static/uploads/profiles/…`

### Extraction OCR
- **4 modèles** : `paddleocr`, `docling`, `easyocr`, `trocr`
- Formats acceptés : images (png, jpg, jpeg, bmp, tiff, webp), **PDF**, txt, docx/doc, xlsx/xls — taille max **10 Mo** (réglable)
- Extraction **un modèle** (sync) ou **tous les modèles** (async recommandé)
- Mode sync `extract-all` conservé pour tests / compatibilité
- Préparation partagée : PDF→images **une seule fois**, resize max côté **1800 px**
- **Warmup** des modèles au démarrage (thread daemon)
- Exécution parallèle (`ThreadPoolExecutor`)
- Sauvegarde de chaque résultat dans `ocr_history`
- Traduction du texte (API MyMemory, détection auto de langue)

### Interface OCR
- Upload glisser-déposer
- Badges modèles, scores, temps, caractères / mots
- Texte coloré par confiance (noir / orange / rouge)
- Mode **Modifier** : mots retouchés passent en noir (même si le texte est identique)
- Enregistrer / Annuler l’édition
- Copier / télécharger le texte
- Traduction inline (sélecteur de langue)
- Bouton **Nouveau Document** : reset UI + effacement de l’état stocké

### Jobs asynchrones & multi-pages
- `POST /api/extract-all` → `job_id` immédiat
- Traitement en **thread serveur** (survit au changement de page)
- Suivi : `GET …/jobs/active`, `GET …/jobs/{job_id}`
- **SharedWorker** `ocr-job-worker.js` : polling ~2 s, diffusion multi-onglets
- Hot-reload **désactivé par défaut** pour ne pas tuer les jobs

### Persistance & navigation
- État d’extraction conservé en `localStorage` (lié au token)
- Conservé lors de la navigation interne (Dashboard, Historique, Rapports)
- **Effacé** : F5 / rechargement de `/app/ocr`, « Nouveau Document », logout / autre compte

### Notifications
- Cloche fixe en haut à droite sur les pages `/app/*`
- Historique local (max 30), badge non lus, Tout lu / Vider
- Types : extraction en cours / terminée / échouée
- Toast + notification navigateur (si permission)

### Dashboard
- KPI : extractions, taux de succès, temps moyen, score global
- Tableau de performances par modèle
- Actions rapides vers OCR, historique, rapports
- Téléchargement rapport local en **PDF uniquement**

### Historique
- Liste des extractions (limite API configurable)
- Filtres modèle + statut (côté client)
- Aperçu texte, scores, modal document (image/PDF) + texte complet
- Copier / télécharger `.txt`

### Rapports
- **Benchmark Local** : stats personnelles par modèle + conseils OLM — export **PDF**
- **Rapport OLM Global** : matrice olmOCR-Bench (AI2), méthodologie, top modèles — export **PDF**
- Les anciens formats Word / Excel / CSV ne sont **plus proposés** à l’UI (routes de téléchargement retirées)

### Infrastructure
- FastAPI + Uvicorn
- MySQL 8 (fallback SQLite automatique)
- SMTP (Gmail recommandé) ; sans config valide → emails en console
- CORS ouvert (dev)
- Static `/static`, uploads `/uploads`

---

## 2. Architecture

```
ocr_project/
├── app/
│   ├── main.py                 # FastAPI, CORS, mounts, startup (SMTP + DB + warmup), /health, /models
│   ├── config/settings.py      # .env, DB, JWT, SMTP, chemins, limites
│   ├── models/                 # SQLAlchemy : User, OTPCode, OCRHistory, database.py
│   ├── schemas/                # Pydantic : auth, user, dashboard
│   ├── routers/
│   │   ├── pages.py            # Pages HTML
│   │   ├── auth.py             # Inscription, OTP, reset
│   │   ├── users.py            # /api/me, avatar
│   │   ├── ocr.py              # extract, extract-all async, translate
│   │   ├── history.py
│   │   ├── dashboard.py
│   │   ├── local_benchmark.py  # data + PDF
│   │   ├── olm_report.py       # data + html + PDF + preview
│   │   └── smtp_admin.py       # présent mais NON monté dans main.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   ├── user_service.py
│   │   ├── ocr_service.py
│   │   ├── extraction_jobs.py  # Jobs OCR arrière-plan
│   │   ├── benchmark_service.py
│   │   ├── local_benchmark_service.py
│   │   └── olm_report_service.py
│   ├── utils/                  # workers OCR, confiance, langue, matrices
│   └── static/
│       ├── pages/              # login, register, dashboard, ocr, …
│       ├── css/theme.css
│       └── js/app.js, ocr-job-worker.js, benchmark_download.js
├── scripts/                    # benchmarks / utilitaires
├── tests/
├── uploads/                    # Fichiers OCR uploadés
├── start_app.py
├── requirements.txt
├── .env.example
└── README.md
```

**Flux :** UI (`static`) → `routers` → `services` → `models` / `utils` → réponse (`schemas`).

| Couche | Rôle |
|--------|------|
| `config/` | Paramètres (.env, DB, JWT, SMTP, chemins) |
| `models/` | Tables ORM |
| `schemas/` | Validation JSON |
| `routers/` | Endpoints HTTP / pages |
| `services/` | Métier (OCR, auth, email, jobs, rapports) |
| `utils/` | Workers OCR, confiance, langue, matrices |
| `static/` | Frontend |

---

## 3. Prérequis

- Python **3.10+**
- MySQL **8** (XAMPP / WAMP / serveur) — fallback SQLite si MySQL indisponible
- Compte email SMTP (Gmail + mot de passe d’application recommandé)
- **WeasyPrint** pour générer les PDF de rapports (`pip install weasyprint`)

---

## 4. Installation

```powershell
cd C:\Users\MSI\Desktop\ocr_project

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install weasyprint

pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

pip install sentencepiece tiktoken

copy .env.example .env

```

Créer la base MySQL `ocr_intelligence` (utf8mb4) ou laisser l’app initialiser / basculer sur SQLite.

---

## 5. Configuration (.env)

Fichier modèle : `.env.example`

| Variable | Description | Défaut typique |
|----------|-------------|----------------|
| `DB_HOST` | Hôte MySQL | `localhost` |
| `DB_PORT` | Port | `3306` |
| `DB_USER` | Utilisateur | `root` |
| `DB_PASSWORD` | Mot de passe | (vide) |
| `DB_NAME` | Nom de la base | `ocr_intelligence` |
| `JWT_SECRET_KEY` | Secret de signature JWT | **à changer** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée du token | `10080` (7 jours) |
| `APP_BASE_URL` | URL publique (liens email) | `http://localhost:8000` |
| `SMTP_HOST` | Serveur SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | 587 (STARTTLS) ou 465 (SSL) | `587` |
| `SMTP_USER` | Compte SMTP | |
| `SMTP_PASSWORD` | Mot de passe d’application | |
| `SMTP_FROM` | Expéditeur | |
| `SMTP_FROM_NAME` | Nom affiché | `OCR Intelligence` |
| `OTP_EXPIRY_MINUTES` | Validité OTP | `10` |
| `OTP_MAX_ATTEMPTS` | Essais max | `3` |

Limite d’upload : `MAX_FILE_SIZE` dans `app/config/settings.py` (défaut **10 Mo**).

Sans SMTP complet au démarrage : les emails sont loggés en console (mode dégradé).

---

## 6. Démarrage

```powershell
.\venv\Scripts\Activate.ps1
python start_app.py
```

| Flag | Défaut | Notes |
|------|--------|-------|
| `--host` | `127.0.0.1` | Adresse d’écoute |
| `--port` | `8000` | Port |
| `--reload` | **OFF** | Dev UI uniquement — **interrompt les jobs OCR** |
| `--no-reload` | — | Alias explicite du comportement par défaut |

- Interface : http://127.0.0.1:8000  
- API Docs : http://127.0.0.1:8000/docs  
- Dashboard : http://127.0.0.1:8000/app  

Au démarrage : chargement SMTP → `init_db()` → warmup OCR en arrière-plan.

---

## 7. Pages & navigation

| URL | Fichier | Description |
|-----|---------|-------------|
| `/` | `login.html` | Connexion |
| `/register` | `register.html` | Inscription |
| `/verify-email` | `verify-email.html` | Activation compte |
| `/reset-password` | `reset-password.html` | Nouveau mot de passe |
| `/app` | `dashboard.html` | Tableau de bord |
| `/app/ocr` | `ocr.html` | Extraction OCR |
| `/app/history` | `history.html` | Historique |
| `/app/profile` | `profile.html` | Profil |
| `/app/local-benchmark` | `local-benchmark.html` | Benchmark Local |
| `/app/olm-benchmark` | `olm-benchmark.html` | Rapport OLM Global |

Sidebar unifiée : **Navigation** (Dashboard, OCR, Historique, Profil) + **Rapports** (Local, OLM).  
Assets : `/static/*` · fichiers uploadés : `/uploads/*`.  
Pages HTML : `Cache-Control: no-store`.

---

## 8. Flux d’authentification

```
Inscription
    → email de vérification (24 h)
    → GET /api/verify-email?token=…
    → compte actif + OTP envoyé
    → saisie OTP → JWT

OU

Connexion (compte déjà vérifié)
    → POST /api/login → OTP envoyé
    → POST /api/verify-otp → JWT
```

Si email non vérifié à la connexion : **403** + possibilité de `POST /api/resend-verification`.

---

## 9. Profil utilisateur

| Méthode | Endpoint | Détail |
|---------|----------|--------|
| GET | `/api/me` | id, email, prénom, nom, avatar, is_active, created_at, last_login |
| PUT | `/api/me` | Mise à jour profil / mot de passe |
| POST | `/api/me/avatar` | Upload avatar (≤ 5 Mo) |

---

## 10. Extraction OCR

### Modèles

| ID | Nom | Formats principaux | Particularité |
|----|-----|--------------------|---------------|
| `paddleocr` | PaddleOCR | image, pdf | Rapide / robuste |
| `docling` | Docling | image, pdf, txt, docx, xlsx | Structure / Markdown |
| `easyocr` | EasyOCR | image, pdf | Multi-langues |
| `trocr` | TrOCR | image, pdf | Transformer (lignes) |

### Comportement technique
- Warmup au startup (`warmup_all_models`)
- Préparation partagée PDF/images (max **1800 px**)
- Docling peut garder le PDF original quand pertinent
- Résultats + scores (précision, robustesse, score global, langue, temps) enregistrés en base

---

## 11. Jobs asynchrones & SharedWorker

1. Upload → `POST /api/extract-all` → `{ job_id, async: true }`
2. Thread serveur : `queued` → `running` → `completed` / `failed`
3. SharedWorker + polling (~2 s) : suivi même si l’utilisateur change de page
4. Fin → notification + affichage / restauration des résultats

Fichiers : `app/services/extraction_jobs.py`, `app/routers/ocr.py`, `app/static/js/ocr-job-worker.js`, `app/static/js/app.js`.

Mode bloquant (tests) : `POST /api/extract-all/sync`.

---

## 12. Persistance extraction (localStorage)

| Clé | Rôle |
|-----|------|
| `ocrExtractionState` | Résultats + éditions (scopé au token) |
| `ocrAppNotifications` | Historique cloche (max 30) |
| `ocrActiveJob` / `ocrNotifiedJobs` | Suivi job multi-pages |
| `access_token`, `token_type`, `user_data` | Session |

| Action | Effet sur l’extraction |
|--------|-------------------------|
| Navigation interne (/app/…) | **Conservée** |
| F5 sur `/app/ocr` | **Effacée** |
| « Nouveau Document » | **Effacée** |
| Logout / autre compte | **Effacée** (+ notifs / jobs) |

---

## 13. Notifications

- Cloche (`app-notif-bell`) sur toutes les pages `/app`
- `notifyExtractionStarted(filename)` → ⏳
- `notifyExtractionComplete(data)` → ✅ (succès modèles, meilleur modèle, durée)
- `notifyExtractionFailed(error, filename)` → ❌
- Panel : liste, Tout lu, Vider
- Toast + notification navigateur optionnelle

---

## 14. Édition & couleurs de confiance

| Confiance | Couleur | Signification |
|-----------|---------|---------------|
| ≥ 90 % | Noir `#111827` | Correct |
| 70–89 % | Orange `#F59E0B` | Probable erreur |
| < 70 % | Rouge `#EF4444` | Faux |

En mode édition, un mot **touché** passe en noir (confiance 100 % visuelle), même sans changement de texte.  
Analyse côté serveur : `app/utils/confidence_analyzer.py`.

---

## 15. Traduction

`POST /api/translate` — body form : `text` ou `file`, `target_lang`, `source_lang` optionnel, `model` optionnel.

Langues : en, es, de, it, ar, fr, pt, ja, zh, ru, ko, tr, nl, pl, vi.  
Moteur : **MyMemory** ; détection auto ; gestion quota (`quota_exceeded`).

---

## 16. Historique

### API
| Méthode | Endpoint | Notes |
|---------|----------|-------|
| GET | `/api/history` | `limit` (≤200, défaut 50), `model`, `status` |
| GET | `/api/history/stats` | Agrégats + derniers résultats |

### UI
Filtres modèle / statut, cartes, modal aperçu document + texte, copier, télécharger `.txt`.

---

## 17. Dashboard

### API
| Méthode | Endpoint | Notes |
|---------|----------|-------|
| GET | `/api/dashboard/stats` | KPI utilisateur |
| GET | `/api/dashboard/export/excel` | API encore présente (non utilisée par le bouton principal UI) |
| GET | `/api/dashboard/export/csv` | Idem |
| GET | `/api/dashboard/benchmark/global` | HTML legacy si fichier présent |

### UI
KPI, tableau par modèle, actions rapides, bouton **Télécharger PDF** → benchmark local.

---

## 18. Rapports benchmark (PDF)

### Benchmark Local — `/api/local-benchmark`
| Méthode | Endpoint |
|---------|----------|
| GET | `/data` |
| GET | `/download/pdf` |

Contenu PDF : extractions totales, taux de succès, précision / temps / score moyens, meilleur modèle, tableau par modèle, notes / comparaison OLM.

### Rapport OLM Global — `/api/olm-report`
| Méthode | Endpoint |
|---------|----------|
| GET | `/data?include_user_stats=` |
| GET | `/html?include_user_stats=` |
| GET | `/download/pdf?include_user_stats=` |
| GET | `/preview` |

Contenu : métadonnées olmOCR-Bench (AI2), méthodologie, matrice de scores, leaders par catégorie, analyse top modèles, stats utilisateur optionnelles.

**UI :** bouton unique **Télécharger PDF** (plus de Word / Excel / CSV).

Dépendance : **WeasyPrint**.

---

## 19. API REST (liste complète)

Préfixe authentifié : header `Authorization: Bearer <token>` (sauf auth publique).

### Général
| Méthode | Chemin | Auth |
|---------|--------|------|
| GET | `/health` | Non |
| GET | `/models` | Non |
| GET | `/docs` · `/redoc` | Non |

### Auth (`/api`)
| Méthode | Chemin |
|---------|--------|
| POST | `/api/register` |
| GET | `/api/verify-email?token=` |
| POST | `/api/resend-verification` |
| POST | `/api/login` |
| POST | `/api/verify-otp` |
| POST | `/api/resend-otp` |
| POST | `/api/forgot-password` |
| POST | `/api/reset-password` |
| POST | `/api/logout` |

### Utilisateur
| Méthode | Chemin |
|---------|--------|
| GET | `/api/me` |
| PUT | `/api/me` |
| POST | `/api/me/avatar` |

### OCR
| Méthode | Chemin |
|---------|--------|
| GET | `/api/models` |
| POST | `/api/extract` |
| POST | `/api/extract-all` |
| GET | `/api/extract-all/jobs/active` |
| GET | `/api/extract-all/jobs/{job_id}` |
| POST | `/api/extract-all/sync` |
| POST | `/api/translate` |

### Historique & dashboard
| Méthode | Chemin |
|---------|--------|
| GET | `/api/history` |
| GET | `/api/history/stats` |
| GET | `/api/dashboard/stats` |
| GET | `/api/dashboard/export/excel` |
| GET | `/api/dashboard/export/csv` |
| GET | `/api/dashboard/benchmark/global` |

### Rapports
| Méthode | Chemin |
|---------|--------|
| GET | `/api/local-benchmark/data` |
| GET | `/api/local-benchmark/download/pdf` |
| GET | `/api/olm-report/data` |
| GET | `/api/olm-report/html` |
| GET | `/api/olm-report/download/pdf` |
| GET | `/api/olm-report/preview` |



Documentation interactive : `/docs`.

---

## 20. Base de données

Moteur : MySQL via `DATABASE_URL` ; fallback **SQLite** `ocr_database.db`.  
Initialisation + migrations légères au startup (`init_db`).

### `users`
`id`, `email`, `password_hash`, `first_name`, `last_name`, `profile_image`, `is_active`, `is_email_verified`, `email_verification_token`, `email_verification_token_expiry`, `reset_token`, `reset_token_expiry`, `created_at`, `last_login`

### `otp_codes`
`id`, `user_id`, `otp_token`, `code_hash`, `expires_at`, `is_used`, `attempts`, `created_at`

### `ocr_history`
`id`, `user_id`, `filename`, `file_type`, `file_path`, `model_id`, `model_name`, `extracted_text`, `char_count`, `word_count`, `execution_time` / `ocr_time_s`, `init_time_s`, `confidence_score`, `precision_score`, `robustness`, `global_score`, `detected_language`, `status`, `error_message`, `client_ip`, `processed_at`

---

## 21. Stack technique

| Domaine | Technologies |
|---------|----------------|
| Backend | FastAPI, Uvicorn, SQLAlchemy 2, Pydantic 2, PyJWT |
| OCR | PaddleOCR, Docling, EasyOCR, TrOCR (Transformers + PyTorch) |
| Images / docs | OpenCV, Pillow, PyMuPDF, img2pdf, openpyxl |
| DB | MySQL 8 / SQLite, PyMySQL |
| Email | SMTP STARTTLS / SSL |
| Frontend | HTML / CSS / JS (Inter), SharedWorker |
| PDF rapports | WeasyPrint |
| Tests | pytest, httpx |

Voir `requirements.txt` pour les versions épinglées.

---

## 22. Scripts & tests

```powershell

pytest tests/ -q

python scripts/run_all_benchmarks.py
python scripts/generate_olm_report.py
python scripts/run_all_multiformat_tests.py
```

Tests présents : moteurs OCR (image / texte / multiformat), email, MySQL, endpoints benchmark (`tests/test_benchmark_endpoints.py` — script manuel, nécessite serveur démarré).

---

## 23. Dépannage

| Problème | Solution |
|----------|----------|
| Emails non reçus | Vérifier `.env` SMTP + mot de passe d’application Gmail |
| Extraction coupée en changeant de page | Lancer **sans** `--reload` + Ctrl+F5 |
| PDF rapport échoue | `pip install weasyprint` (+ dépendances système si besoin) |
| TrOCR échoue | `pip install sentencepiece tiktoken` |
| MySQL down | L’app bascule sur SQLite automatiquement |
| Avatar 404 | Chemins `/uploads/avatars/…` ou `/static/uploads/profiles/…` |
| Port 8000 occupé | `python start_app.py --port 8001` |
| OTP expiré / max essais | `POST /api/resend-otp` ou se reconnecter |
| Accents / emojis cassés dans l’UI | Fichiers HTML doivent être **UTF-8** ; Ctrl+F5 |

---

## 24. Auteur

**Kinza Chaouachi** — OCR Intelligence v3.0  
GitHub : [Kinzaachaouachi/ocr_project](https://github.com/Kinzaachaouachi/ocr_project)

