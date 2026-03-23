# Contribuer au projet Veille IA Wavestone

## Prérequis

- Python 3.10+
- Git

## Installation locale

```bash
git clone https://github.com/Aliquanto3/veille-ia-wavestone.git
cd veille-ia-wavestone
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Configuration

Créer un fichier `.env` à la racine :

```env
MISTRAL_API_KEY="votre_cle_api_ici"
# Optionnel : override du modèle (défaut : mistral-small-2603)
# MISTRAL_MODEL="mistral-large-latest"
```

La clé API Mistral est également stockée dans les **GitHub Secrets** (`MISTRAL_API_KEY`) pour le workflow de déploiement automatique.

## Structure du projet

```
veille_ia/           ← Package principal
├── __main__.py      ← Point d'entrée CLI
├── config.py        ← Constantes et configuration
├── models.py        ← Dataclass NewsItem
├── sources.py       ← Protocol NewsSource + implémentations (txt, excel, db)
├── parsers/         ← Parsers par format
├── database.py      ← Couche SQLite
├── enhancer.py      ← LLM Protocol + Mistral + Teams report
├── renderer.py      ← Génération HTML
├── utils.py         ← Utilitaires
└── assets/          ← CSS et JS externalisés

tests/               ← Tests pytest
generate_veille.py   ← Wrapper rétrocompatible
generate_portal.py   ← Gestionnaire du portail d'archives
```

## Commandes de développement

```bash
# Lancer le pipeline (mode no-API pour tester)
python -m veille_ia --no-mistral

# Linter
ruff check veille_ia/ tests/

# Type checking
mypy veille_ia/ --ignore-missing-imports

# Tests
pytest tests/ -v

# Tout d'un coup (reproduit ce que fait la CI)
ruff check veille_ia/ && mypy veille_ia/ --ignore-missing-imports && pytest tests/ -v
```

## Workflow de contribution

1. Créer une branche depuis `main` : `git checkout -b feature/ma-feature`
2. Développer + ajouter des tests
3. Vérifier localement : `ruff check && pytest`
4. Pousser + ouvrir une Pull Request
5. La CI GitHub Actions vérifie automatiquement : lint, types, tests, dry-run

## Workflow de publication hebdomadaire

### Option A : Automatique (CI/CD)

1. Remplir le fichier Excel dans `inputs/` avec les nouvelles actualités
2. Commit + push sur `main`
3. Le workflow `deploy_veille.yml` se déclenche automatiquement
4. Le dashboard HTML et le message Teams sont générés et commités

### Option B : Manuel

```bash
# Depuis Excel
python -m veille_ia --excel inputs/Veille_IA_Template.xlsx --db

# Depuis la BDD (toutes les données)
python -m veille_ia --from-db -o Veille_IA_Complete.html

# Mettre à jour le portail
python generate_portal.py

# Publier
git add . && git commit -m "Nouvelle veille" && git push
```

## Gestion des secrets

| Secret | Où | Usage |
|---|---|---|
| `MISTRAL_API_KEY` | `.env` (local) | Appels API Mistral en local |
| `MISTRAL_API_KEY` | GitHub Secrets | Appels API dans le workflow CI/CD |

Ne jamais commiter le fichier `.env`. Il est dans le `.gitignore`.
