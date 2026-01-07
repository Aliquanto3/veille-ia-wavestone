# 🤖 Veille IA Generator - Wavestone

Ce projet est une suite d'outils d'automatisation destinée aux consultants IA de Wavestone. Il transforme des notes de veille brutes en un **Dashboard HTML interactif**, enrichi par **Mistral Large 3**, et maintient un **Portail d'Archives** organisé.

Le site web est disponible ici : [https://aliquanto3.github.io/veille-ia-wavestone/](https://aliquanto3.github.io/veille-ia-wavestone/)

## 🎯 Objectifs

1.  **Industrialisation** : Automatisation complète du parsing, de l'enrichissement et du déploiement.
2.  **Expérience Utilisateur (UX)** : Interface "Kanban" filtrable, responsive, avec "Copy for Teams" et mode sombre.
3.  **Productivité** : Génération automatique d'un message d'annonce ("Teasing") pour Microsoft Teams, rédigé par l'IA.
4.  **Archivage Structuré** : Séparation nette entre les pages Web, les textes d'annonces et les logs de debug.

## 🏗 Architecture du Projet

Le projet suit une structure stricte pour garantir la maintenabilité :

```text
.
├── inputs/
│   └── 2026-01-05_2026-01-12/      <-- Dossier hebdomadaire (Source)
│       ├── Marché.txt
│       └── Tech.txt
│
├── outputs/                        <-- Dossier de génération (Destination)
│   ├── pages/                      <-- Dashboards HTML (Publiés)
│   │   └── Veille_IA_2026-01-12.html
│   ├── Teams/                      <-- Messages d'annonces (Publiés)
│   │   └── Annonce_Teams_du_05-01...txt
│   └── TexteMistral/               <-- Logs JSON bruts (Ignorés par Git)
│
├── index.html                      <-- Portail d'accueil (Racine)
├── generate_veille.py              <-- Moteur de génération
├── generate_portal.py              <-- Gestionnaire du portail
└── requirements.txt
```

## ⚙️ Installation

1.  **Cloner et préparer l'environnement**
    ```bash
    git clone [https://github.com/votre-repo/veille-ia-wavestone.git](https://github.com/votre-repo/veille-ia-wavestone.git)
    cd veille-ia-wavestone
    python -m venv venv
    # Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configuration API**
    Créez un fichier `.env` à la racine :
    ```env
    MISTRAL_API_KEY="votre_cle_api_ici"
    ```

## 📝 Format des Inputs

Chaque semaine, créez un dossier dans `inputs/` au format `YYYY-MM-DD_YYYY-MM-DD` (ex: `2026-01-05_2026-01-12`).
Les fichiers `.txt` à l'intérieur doivent suivre ce format :

```text
**CATEGORIE :** Marché
**SOUS-CATEGORIE :** Stratégie
**TITRE :** Titre de l'actualité
**DESCRIPTION :** Texte descriptif.
**SOURCES :**
- [https://lien-source.com](https://lien-source.com)
```
*Si les catégories sont manquantes, l'IA les déduira.*

## ▶️ Workflow Hebdomadaire

### Option A : Automatisation GitHub (CI/CD)
1.  Créez le dossier daté dans `inputs/` et ajoutez vos fichiers.
2.  Commitez et poussez sur GitHub.
3.  **L'Action GitHub** génère tout, met à jour le site et affiche le message Teams dans le résumé du Job.

### Option B : Exécution Manuelle (Local)

1.  **Lancer la génération**
    Le script détecte automatiquement le dossier le plus récent dans `inputs/`.
    ```bash
    python generate_veille.py
    ```
    * Le HTML est créé dans `outputs/pages/`.
    * Le message Teams est créé dans `outputs/Teams/`.
    * Les logs JSON sont dans `outputs/TexteMistral/`.

2.  **Mettre à jour le portail**
    ```bash
    python generate_portal.py
    ```
    *Scanne `outputs/pages/` et met à jour `index.html`.*

3.  **Publier**
    ```bash
    git add .
    git commit -m "Nouvelle veille S2"
    git push
    ```

## 🎛 Arguments CLI (`generate_veille.py`)

| Argument | Description |
| :--- | :--- |
| `--no-mistral` | Désactive l'IA (Rapide/Gratuit). |
| `--save-json` | Force la sauvegarde JSON (activé par défaut si besoin de debug). |
| `-o`, `--output` | Nom du fichier HTML final (Défaut: `Veille_IA_DATE.html`). |
| `--date-start` | Force une date de début (cherche le dossier correspondant). |
| `--input-dir` | Change le dossier racine des inputs (Défaut: `inputs`). |

---
*Projet interne - Wavestone AI & Nantes Business Units.*