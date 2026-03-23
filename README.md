# 🤖 Veille IA Generator - Wavestone

Pipeline Python automatisé transformant des actualités IA en **dashboard HTML interactif**, enrichi par **Mistral Small 4** (`mistral-small-2603`). Supporte l'ingestion depuis Excel, fichiers texte ou base SQLite, avec historisation et filtrage temporel.

Le site web est disponible ici : [Portail Veille IA - Wavestone](https://aliquanto3.github.io/veille-ia-wavestone/)

## 🎯 Objectifs

1. **Industrialisation** : Pipeline complet parsing → enrichissement LLM → dashboard HTML → déploiement automatique.
2. **Multi-sources** : Ingestion depuis Excel (saisie manuelle), fichiers .txt (legacy), BDD SQLite (agents automatisés, RSS — à venir).
3. **Expérience Utilisateur** : Interface Kanban filtrable par catégorie, sous-catégorie, texte libre et plage de dates.
4. **Productivité** : Génération automatique d'un message d'annonce Teams rédigé par l'IA.
5. **Historisation** : Toutes les news stockées en BDD SQLite avec import incrémental et déduplication.

## 🏗 Architecture du Projet

```text
.
├── veille_ia/                      <-- Package Python principal
│   ├── __main__.py                 <-- Point d'entrée CLI
│   ├── config.py                   <-- Constantes et configuration centralisée
│   ├── models.py                   <-- Dataclass NewsItem
│   ├── sources.py                  <-- Protocol NewsSource + TxtSource / ExcelSource / DbSource
│   ├── parsers/
│   │   ├── txt_parser.py           <-- Parser fichiers .txt (format Markdown-like)
│   │   └── excel_reader.py         <-- Lecteur Excel (onglets NEWS + _DATA)
│   ├── database.py                 <-- Couche SQLite (CRUD, migrations, ingestion multi-sources)
│   ├── enhancer.py                 <-- Protocol LLMClient + Mistral + enrichissement + Teams report
│   ├── renderer.py                 <-- Génération HTML du dashboard
│   ├── utils.py                    <-- Résolution de dossiers, formatage de dates
│   └── assets/
│       ├── style.css               <-- Styles du dashboard (externalisé)
│       └── script.js               <-- Filtres JS côté client (externalisé)
│
├── tests/                          <-- Tests pytest (27 tests)
├── inputs/                         <-- Fichiers source (Excel ou .txt)
├── outputs/
│   ├── pages/                      <-- Dashboards HTML générés
│   ├── Teams/                      <-- Messages d'annonce Teams
│   └── TexteMistral/               <-- Logs JSON debug (ignorés par Git)
│
├── generate_veille.py              <-- Wrapper rétrocompatible → python -m veille_ia
├── generate_portal.py              <-- Gestionnaire du portail d'archives
├── deploy.bat                      <-- Script de déploiement Windows
├── requirements.txt                <-- Dépendances production
├── requirements-dev.txt            <-- Dépendances développement (ruff, mypy, pytest)
├── CONTRIBUTING.md                 <-- Guide de contribution
└── .github/workflows/
    ├── deploy_veille.yml           <-- CI/CD : génération + déploiement automatique
    └── ci.yml                      <-- CI : lint, types, tests, dry-run
```

## 📋 Vocabulaire Contrôlé

Le pipeline utilise un vocabulaire contrôlé pour la classification. En mode Excel, ces listes sont extensibles via l'onglet `_DATA` du fichier source. Valeurs par défaut :

- **Catégories** : `Marché`, `Tech`, `Gouvernance`
- **Sous-catégories** : `Souveraineté`, `M&A`, `Conseil`, `Stratégie`, `Economie`, `Modèles`, `Providers`, `Développement`, `Robotique`, `Evaluation`, `RSE`, `Cybersécurité`, `Conformité`, `RH`

## ⚙️ Installation

```bash
git clone https://github.com/Aliquanto3/veille-ia-wavestone.git
cd veille-ia-wavestone
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# Pour le développement (lint, tests, type check) :
pip install -r requirements-dev.txt
```

Créer un fichier `.env` à la racine :

```env
MISTRAL_API_KEY="votre_cle_api_ici"
# Optionnel : override du modèle (défaut : mistral-small-2603)
# MISTRAL_MODEL="mistral-large-latest"
```

## 📝 Sources de données

### Option 1 : Fichier Excel (recommandé)

Le fichier Excel comporte deux onglets :

- **`_DATA`** : Vocabulaire contrôlé (catégories et sous-catégories). Menus déroulants dans l'onglet NEWS.
- **`NEWS`** : Saisie des actualités avec les colonnes `Catégorie`, `Sous-catégorie`, `Titre`, `Description`, `Sources`, `Date`.

Un template pré-rempli est fourni dans `inputs/`.

### Option 2 : Fichiers .txt (legacy)

Créer un dossier dans `inputs/` au format `YYYY-MM-DD_YYYY-MM-DD` contenant des fichiers `.txt` :

```text
**CATEGORIE :** Marché
**SOUS-CATEGORIE :** Stratégie
**TITRE :** Titre de l'actualité
**DESCRIPTION :** Texte descriptif.
**SOURCES :**
- https://lien-source.com
```

### Option 3 : Base de données SQLite

Les news historisées en BDD peuvent être rechargées directement avec `--from-db`. Cette option est aussi le point d'entrée prévu pour les sources automatisées futures (agents IA, flux RSS).

## ▶️ Utilisation

```bash
# Depuis un fichier Excel (mode recommandé)
python -m veille_ia --excel inputs/Veille_IA_Template.xlsx

# Depuis Excel + stockage en BDD (import incrémental)
python -m veille_ia --excel inputs/Veille_IA_Template.xlsx --db

# Dashboard depuis la BDD (toutes les données historisées)
python -m veille_ia --from-db

# Dashboard depuis la BDD (filtré par dates)
python -m veille_ia --from-db --date-start 2025-12-01 --date-end 2025-12-31

# Depuis des fichiers .txt (legacy, auto-détection du dossier le plus récent)
python -m veille_ia

# Mode sans appel API (test rapide)
python -m veille_ia --excel inputs/Veille_IA_Template.xlsx --no-mistral

# Wrapper rétrocompatible (même comportement)
python generate_veille.py --no-mistral
```

Après génération, mettre à jour le portail d'archives :

```bash
python generate_portal.py
```

## 🎛 Arguments CLI

| Argument | Description |
| :--- | :--- |
| `--no-mistral` | Désactive les appels LLM (rapide/gratuit). |
| `--save-json` | Sauvegarde les données brutes en JSON (debug). |
| `-o`, `--output` | Nom du fichier HTML (défaut: `Veille_IA_DATE.html`). |
| `--date-start` | Date de début `YYYY-MM-DD`. |
| `--date-end` | Date de fin `YYYY-MM-DD`. |
| `--title` | Titre du dashboard (défaut: `🤖 Veille IA Wavestone`). |
| `--subtitle` | Sous-titre personnalisé. |
| `--input-dir` | Dossier racine des inputs .txt (défaut: `inputs`). |
| `--excel` | Fichier Excel source (remplace les .txt). |
| `--db` | Stocke les news en BDD SQLite après ingestion. |
| `--db-path` | Chemin de la BDD (défaut: `data/veille_ia.db`). |
| `--from-db` | Génère le dashboard depuis la BDD. |

## 🗄️ Base de données

SQLite, fichier `data/veille_ia.db` (créé automatiquement, ignoré par Git).

### Schéma de la table `news`

| Colonne | Type | Description |
|---|---|---|
| `uid` | TEXT PK | Identifiant unique (généré) |
| `category` | TEXT | Catégorie principale |
| `sub_category` | TEXT | Sous-catégorie |
| `title` | TEXT | Titre de l'actualité |
| `description` | TEXT | Corps (peut contenir du HTML si enrichi par LLM) |
| `links` | TEXT | URLs séparées par `\n` |
| `date` | TEXT | Date YYYY-MM-DD (indexée) |
| `is_enhanced` | INTEGER | 1 si enrichi par LLM |
| `source` | TEXT | Identifiant de provenance (ex: `manual:excel`, `rss:techcrunch`) |
| `created_at` | TEXT | Timestamp d'insertion |
| `updated_at` | TEXT | Timestamp de dernière mise à jour |

Index : `date`, `category`, `source`.

Déduplication : par `titre + date` — un même article avec le même titre et la même date est mis à jour, pas dupliqué.

### Ingestion multi-sources

L'API publique pour l'ingestion est `NewsDatabase.ingest(items, source="identifiant")`. Chaque source tague ses items avec un identifiant unique, permettant de tracer la provenance et de filtrer par source à terme.

| Source | Identifiant | Statut |
|---|---|---|
| Saisie Excel manuelle | `manual:excel` | ✅ Implémenté |
| Fichiers .txt legacy | `manual:txt` | ✅ Implémenté |
| Flux RSS | `rss:<nom_flux>` | 🔜 À venir |
| Agent IA web | `agent:<nom_agent>` | 🔜 À venir |

## 🧪 Développement

```bash
# Lint
ruff check veille_ia/ tests/

# Type check
mypy veille_ia/ --ignore-missing-imports

# Tests (27 tests)
pytest tests/ -v

# Dry-run complet (sans appel API)
python -m veille_ia --no-mistral --save-json
```

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour le guide de contribution complet.

## 🔄 CI/CD

Deux workflows GitHub Actions :

- **`ci.yml`** : Lint + types + tests + dry-run sur chaque push/PR vers `main`.
- **`deploy_veille.yml`** : Génération automatique du dashboard + commit + déploiement quand le contenu de `inputs/` est modifié.

---
*Projet interne — Wavestone AI Practice, Nantes.*
