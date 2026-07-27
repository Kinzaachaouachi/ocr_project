# OCR Intelligence — Plateforme OCR Multi-Modèles

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/Version-3.0.0-purple.svg)](#)

Plateforme web d’extraction OCR avec **4 moteurs en parallèle** (PaddleOCR, Docling, EasyOCR, TrOCR), authentification sécurisée (email + OTP), dashboard, historique, édition colorée par confiance, notifications, et rapports de benchmark (local + OLM Global).

**Dépôt :** https://github.com/Kinzaachaouachi/ocr_project  
**Branche principale de travail :** `ocr`

---

## Table des matières

1. [Fonctionnalités](#1-fonctionnalités)
2. [Architecture](#2-architecture)
3. [Prérequis](#3-prérequis)
4. [Installation](#4-installation)
5. [Configuration](#5-configuration)
6. [Démarrage](#6-démarrage)
7. [Pages & navigation](#7-pages--navigation)
8. [API REST](#8-api-rest)
9. [Base de données](#9-base-de-données)
10. [Extraction OCR asynchrone](#10-extraction-ocr-asynchrone)
11. [Notifications](#11-notifications)
12. [Édition & couleurs de confiance](#12-édition--couleurs-de-confiance)
13. [Rapports & exports](#13-rapports--exports)
14. [Générer le rapport projet](#14-générer-le-rapport-projet)
15. [Scripts & tests](#15-scripts--tests)
16. [Dépannage](#16-dépannage)

---

## 1. Fonctionnalités

### Authentification
- Inscription avec validation email
- Vérification de compte par lien email (24 h)
- Connexion + **OTP 2FA** par email (6 chiffres, 10 min, max 3 essais)
- Mot de passe oublié / réinitialisation
- JWT (session)
- Profil : nom, email, avatar (JPG/PNG/GIF/WEBP, max 5 Mo)

### Extraction OCR
- **4 modèles simultanés** : PaddleOCR, Docling, EasyOCR, TrOCR
- **Job asynchrone** : l’extraction continue même si l’utilisateur change de page
- SharedWorker + polling pour le suivi multi-pages
- Préparation partagée (PDF→images une seule fois, resize max 1800 px)
- Préchargement (warmup) des modèles au démarrage
- Traduction du texte extrait (API `/api/translate`)

### Interface
- Sidebar unifiée (Navigation + Rapports)
- Dashboard (stats, activité récente, exports)
- Historique des extractions (filtre, aperçu, téléchargement)
- Édition OCR colorée (noir / orange / rouge selon confiance)
- Persistance de l’extraction (localStorage) — effacée au F5 OCR ou « Nouveau Document »
- Centre de **notifications** (cloche) lié aux extractions

### Rapports
- **Benchmark Local** : performances de *vos* extractions
- **Rapport OLM Global** : matrice olmOCR-Bench (référence AI2)
- Export **PDF** uniquement (Benchmark Local + OLM Global)

---

## 2. Architecture

```
ocr_project/
├── app/                          # Application FastAPI v3
│   ├── main.py                   # Point d’entrée (startup, routers, static)
│   ├── config/settings.py        # .env, DB, JWT, SMTP, chemins
│   ├── models/                   # SQLAlchemy (User, OTP, OCRHistory)
│   ├── schemas/                  # Pydantic (auth, user, dashboard)
│   ├── routers/                  # Endpoints HTTP
│   │   ├── auth.py               # register, login, OTP, reset
│   │   ├── ocr.py                # extract, extract-all async, translate
│   │   ├── history.py
│   │   ├── dashboard.py
│   │   ├── users.py              # /api/me, avatar
│   │   ├── local_benchmark.py
│   │   ├── olm_report.py
│   │   └── pages.py              # HTML pages
│   ├── services/                 # Logique métier
│   │   ├── ocr_service.py
│   │   ├── extraction_jobs.py    # Jobs OCR arrière-plan
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   ├── local_benchmark_service.py
│   │   └── olm_report_service.py
│   ├── utils/                    # OCR workers, confiance, langue, matrices
│   └── static/                   # Frontend
│       ├── pages/                # HTML (login, dashboard, ocr, …)
│       ├── css/theme.css
│       └── js/app.js, ocr-job-worker.js, …
├── scripts/                      # Utilitaires & génération de rapports
├── tests/
├── uploads/                      # Fichiers uploadés
├── start_app.py                  # Lanceur uvicorn
├── requirements.txt
├── .env.example
└── README.md
```

### Rôles des dossiers `app/`

| Dossier | Rôle |
|---------|------|
| `config/` | Paramètres (.env, DB, SMTP, JWT) |
| `models/` | Tables SQLAlchemy |
| `schemas/` | Validation JSON (Pydantic) |
| `routers/` | Routes HTTP / pages |
| `services/` | Métier (OCR, email, rapports, jobs) |
| `utils/` | Workers OCR, confiance, langue |
| `static/` | UI (HTML/CSS/JS) |

**Flux :** UI (`static`) → `routers` → `services` → `models` / `utils` → réponse (`schemas`).

---

## 3. Prérequis

- Python **3.10+**
- MySQL **8** (XAMPP / WAMP / serveur) — fallback SQLite si MySQL indisponible
- (Optionnel) Compte Gmail + mot de passe d’application pour les emails

---

## 4. Installation

```powershell
cd C:\Users\MSI\Desktop\ocr_project

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# PyTorch CPU (Windows) si besoin :
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# TrOCR
pip install sentencepiece tiktoken
```

Créer la base MySQL `ocr_intelligence` (utf8mb4), ou laisser l’app créer les tables au démarrage.

---

## 5. Configuration

```powershell
copy .env.example .env
```

Variables principales (voir `.env.example`) :

| Variable | Description |
|----------|-------------|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL |
| `JWT_SECRET_KEY` | Secret JWT |
| `APP_BASE_URL` | URL publique (liens email) |
| `SMTP_*` | Serveur email (Gmail recommandé) |
| `OTP_EXPIRY_MINUTES`, `OTP_MAX_ATTEMPTS` | OTP |

Sans SMTP valide, les emails peuvent être affichés en console (mode dégradé).

---

## 6. Démarrage

```powershell
.\venv\Scripts\Activate.ps1
python start_app.py
```

- Interface : http://127.0.0.1:8000  
- Docs API : http://127.0.0.1:8000/docs  
- Dashboard : http://127.0.0.1:8000/app  

**Important :** le hot-reload est **désactivé par défaut** pour ne pas interrompre les jobs OCR.  
Pour le dev UI uniquement : `python start_app.py --reload`

---

## 7. Pages & navigation

| URL | Page |
|-----|------|
| `/` | Connexion |
| `/register` | Inscription |
| `/verify-email` | Activation compte |
| `/reset-password` | Nouveau mot de passe |
| `/app` | Dashboard |
| `/app/ocr` | Extraction OCR |
| `/app/history` | Historique |
| `/app/profile` | Profil |
| `/app/local-benchmark` | Benchmark Local |
| `/app/olm-benchmark` | Rapport OLM Global |

---

## 8. API REST

Préfixe authentifié : header `Authorization: Bearer <token>`

### Auth
- `POST /api/register`
- `GET /api/verify-email?token=…`
- `POST /api/login` → envoi OTP
- `POST /api/verify-otp` → JWT
- `POST /api/resend-otp`
- `POST /api/forgot-password` / `POST /api/reset-password`
- `POST /api/logout`

### Utilisateur
- `GET/PUT /api/me`
- `POST /api/me/avatar`

### OCR
- `GET /api/models`
- `POST /api/extract` — un modèle
- `POST /api/extract-all` — **async** → `{ job_id }`
- `GET /api/extract-all/jobs/active`
- `GET /api/extract-all/jobs/{job_id}`
- `POST /api/extract-all/sync` — mode bloquant (tests)
- `POST /api/translate`

### Historique & dashboard
- `GET /api/history`
- `GET /api/history/stats`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/export/excel|csv`

### Rapports
- `GET /api/local-benchmark/data`
- `GET /api/local-benchmark/download/pdf`
- `GET /api/olm-report/data`
- `GET /api/olm-report/download/pdf`

Documentation interactive : `/docs`

---

## 9. Base de données

Tables principales :

| Table | Contenu |
|-------|---------|
| `users` | Comptes, hash mot de passe, avatar, tokens email/reset |
| `otp_codes` | Codes OTP (hashés) |
| `ocr_history` | Extractions (texte, modèle, scores, fichier) |

Les tables sont créées/alignées au démarrage (`init_db`).

---

## 10. Extraction OCR asynchrone

1. Upload → `POST /api/extract-all` → `job_id` immédiat  
2. Traitement en **thread serveur** (continue si l’utilisateur change de page)  
3. Suivi via **SharedWorker** (`ocr-job-worker.js`) + polling  
4. Fin → notification + résultats persistés (`localStorage`)

Fichiers clés :
- `app/services/extraction_jobs.py`
- `app/routers/ocr.py`
- `app/static/js/ocr-job-worker.js`
- `app/static/js/app.js`

---

## 11. Notifications

- Cloche en haut à droite sur les pages `/app`
- Historique (Tout lu / Vider)
- Types liés à l’OCR : en cours / terminée / échouée
- Toast + notification navigateur (si permission)

Fichiers : `app/static/js/app.js`, `app/static/css/theme.css`, `app/static/pages/ocr.html`

---

## 12. Édition & couleurs de confiance

| Confiance | Couleur | Signification |
|-----------|---------|---------------|
| ≥ 90 % | Noir | Correct |
| 70–89 % | Orange | Probable erreur |
| < 70 % | Rouge | Faux |

En mode **Modifier**, un mot retouché passe en noir (même si le texte reste identique).

---

## 13. Rapports & exports

### Benchmark Local
Statistiques personnelles par modèle (précision, temps, score).

### Rapport OLM Global
Matrice de référence olmOCR-Bench (Allen Institute for AI).

Export : **PDF** uniquement.

---

## 14. Générer le rapport projet

Un script scanne le dépôt et produit un **rapport complet** (Markdown + HTML + Word optionnel) :

```powershell
.\venv\Scripts\Activate.ps1
python scripts/generate_project_report.py
```

Options :

```powershell
python scripts/generate_project_report.py --format all
python scripts/generate_project_report.py --format md
python scripts/generate_project_report.py --format html
python scripts/generate_project_report.py --format docx
python scripts/generate_project_report.py --out reports
```

Sorties typiques dans `reports/` :
- `OCR_Intelligence_Rapport_Projet.md`
- `OCR_Intelligence_Rapport_Projet.html`
- `OCR_Intelligence_Rapport_Projet.docx` (si `python-docx` installé)

Le rapport inclut : description, architecture, arborescence, endpoints, modèles OCR, auth, notifications, jobs async, stack technique, statistiques de fichiers.

---

## 15. Scripts & tests

```powershell
# Tests
pytest tests/ -q

# Rapport projet
python scripts/generate_project_report.py

# Benchmarks / utilitaires (dossier scripts/)
python scripts/run_all_benchmarks.py
```

Lancement recommandé : `python start_app.py` (sans `--reload` en usage OCR réel).

---

## 16. Dépannage

| Problème | Solution |
|----------|----------|
| Emails non reçus | Vérifier `.env` SMTP + mot de passe d’application Gmail |
| TrOCR échoue | `pip install sentencepiece tiktoken` |
| Extraction coupée en changeant de page | Relancer `python start_app.py` **sans** `--reload` + Ctrl+F5 |
| MySQL down | L’app bascule sur SQLite automatiquement |
| Avatar 404 | Chemins `/static/uploads/profiles/…` ou `/uploads/avatars/…` |
| Port 8000 occupé | `python start_app.py --port 8001` |

---

## Stack technique

- **Backend :** FastAPI, Uvicorn, SQLAlchemy, PyJWT, Pydantic  
- **OCR :** PaddleOCR, Docling, EasyOCR, TrOCR (Transformers + PyTorch)  
- **Frontend :** HTML/CSS/JS (Inter), SharedWorker  
- **DB :** MySQL 8 / SQLite fallback  
- **Email :** SMTP (STARTTLS / SSL)

---

## Auteur

**Kinza Chaouachi** — Projet OCR Intelligence v3.0  
GitHub : [Kinzaachaouachi/ocr_project](https://github.com/Kinzaachaouachi/ocr_project)

---



