# 🤖 Veille IA Generator - Wavestone

Ce projet est un outil d'automatisation destiné à la cellule de veille IA de Wavestone. Il permet de transformer des notes de veille brutes (fichiers texte) en un **Dashboard HTML interactif et cognitif**, enrichi par l'IA générative (Mistral Large).

## 🎯 Objectifs

L'objectif est de réduire la friction cognitive pour les consultants lors de la consommation de la veille technologique :
1.  **Centralisation** : Agréger des sources multiples (Tech, Gouvernance, Marché) en un point unique.
2.  **Expérience Utilisateur (UX)** : Offrir une interface de type "Kanban" avec filtres dynamiques et moteur de recherche instantané, plutôt qu'un document linéaire.
3.  **Enrichissement Cognitif** : Utiliser un LLM (Mistral AI) pour corriger, formater (gras, italique) et structurer l'information automatiquement, garantissant une lisibilité maximale.
4.  **Portabilité** : Générer un fichier HTML "Single Page Application" (SPA) autonome, partageable via Teams/Email sans serveur ni authentification complexe.

## 🏗 Architecture Technique

Le projet suit une approche **OOP (Orientée Objet)** et modulaire, respectant les standards de qualité Python (Type Hinting strict, PEP 8).

* **`NewsParser`** : Responsable de l'ingestion. Lit les fichiers `.txt` dans le dossier `inputs/`, nettoie les balises et structure les données via des Regex.
* **`MistralEnhancer`** : Responsable de la couche cognitive. Utilise l'API Mistral en mode **Batch** pour traiter plusieurs actualités simultanément (optimisation de la latence et des quotas). Force le formatage JSON pour la stabilité.
* **`HTMLRenderer`** : Responsable de la présentation. Génère le DOM HTML/CSS/JS. Intègre la logique de filtrage (catégories/sous-catégories) et l'interactivité client-side.
* **Modèle de données** : Utilisation de `dataclasses` pour garantir l'intégrité des objets `NewsItem`.

## ⚙️ Pré-requis

* **Python** : 3.10 ou supérieur.
* **API Key** : Une clé API valide pour [Mistral Platform](https://console.mistral.ai/).

## 🚀 Installation

1.  **Cloner le projet**
    ```bash
    git clone [https://github.com/votre-repo/veille-ia-wavestone.git](https://github.com/votre-repo/veille-ia-wavestone.git)
    cd veille-ia-wavestone
    ```

2.  **Créer un environnement virtuel (Recommandé)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Installer les dépendances**
    ```bash
    pip install -r requirements.txt
    ```
    *Dépendances principales : `mistralai`, `python-dotenv`.*

## 🔧 Configuration

1.  **Variables d'environnement**
    Créez un fichier `.env` à la racine du projet et ajoutez votre clé API :
    ```env
    MISTRAL_API_KEY="votre_cle_api_ici"
    ```

2.  **Dossier d'entrées**
    Assurez-vous que le dossier `inputs/` existe à la racine. Placez-y vos fichiers de veille bruts (format `.txt`).
    *Exemple : `inputs/Tech.txt`, `inputs/Gouvernance.txt`.*

    > **Format des fichiers .txt** :
    > Le script attend des marqueurs spécifiques (`**CATEGORIE :**`, `**TITRE :**`, etc.). Voir les fichiers d'exemple fournis.

## ▶️ Utilisation

Lancez simplement le script principal :

```bash
python generate_veille.py
```

**Le workflow s'exécute en 3 étapes :**
1.  **Parsing** : Lecture de tous les fichiers `.txt` présents dans `inputs/`.
2.  **Enhancement** : Envoi des données par lots (batchs de 10) à Mistral Large pour réécriture et formatage HTML.
3.  **Rendering** : Génération du fichier final `Veille_IA_Enhanced_YYYY-MM-DD.html`.

Ouvrez le fichier HTML généré dans votre navigateur pour consulter la veille.

## 🎛 Usage Avancé (Ligne de commande)

Le script supporte désormais de nombreux arguments pour personnaliser la génération sans toucher au code :

| Argument | Description | Exemple |
| :--- | :--- | :--- |
| `--no-mistral` | Génère le HTML sans appeler l'IA (Rapide & Gratuit) | `python generate_veille.py --no-mistral` |
| `--save-json` | Sauvegarde les données traitées dans un dossier `outputs/` | `python generate_veille.py --save-json` |
| `-o`, `--output` | Choisir le nom du fichier HTML de sortie | `-o "Veille_Semaine_42.html"` |
| `--title` | Personnaliser le grand titre du Dashboard | `--title "Veille Banque & Assurance"` |
| `--date-start` | Date de début de la période couverte | `--date-start "06/01"` |
| `--date-end` | Date de fin de la période couverte | `--date-end "12/01"` |
| `--input-dir` | Changer le dossier source (défaut: `inputs`) | `--input-dir "inputs_finance"` |

**Exemple complet de commande :**
```bash
python generate_veille.py --date-start "01/01" --date-end "07/01" --title "Revue IA Hebdo" --save-json
```

## 🛠 Personnalisation

* **Modifier le modèle IA** : Dans `generate_veille.py`, classe `MistralEnhancer`, changez `model="mistral-large-latest"`.
* **Ajuster le Batch Size** : Modifiez le paramètre `batch_size` lors de l'instanciation de l'enhancer dans le `main()` (défaut : 10).
* **Styling (CSS)** : Le CSS est embarqué dans la classe `HTMLRenderer`. Modifiez la méthode `_get_css` pour ajuster les couleurs (Charte Wavestone).

## 📝 Format des fichiers d'entrée (`inputs/*.txt`)

Pour que le moteur de parsing puisse extraire correctement les données, chaque fichier `.txt` déposé dans le dossier `inputs/` doit respecter une structure stricte basée sur des marqueurs textuels spécifiques.

### Structure type d'un article

```text
**CATEGORIE :** Nom de la catégorie (ex: Gouvernance)
**SOUS-CATEGORIE :** Nom de la sous-catégorie (ex: Conformité)
**TITRE :** Titre de l'actualité
**DESCRIPTION :** Texte descriptif complet. 
Le script supporte les descriptions multi-lignes.
Les balises de type sont automatiquement supprimées lors du traitement.
**SOURCES :**
- https://lien-vers-la-source-1.com
- https://lien-vers-la-source-2.com
```

### Règles de validité (Parsing Regex)

* **Clés de détection** : Les clés doivent être écrites exactement comme suit (gras inclus) : `**CATEGORIE :**`, `**SOUS-CATEGORIE :**`, `**TITRE :**`, `**DESCRIPTION :**` et `**SOURCES :**`.
* [cite_start]**Nettoyage automatique** : Le script est conçu pour ignorer les métadonnées de sourcing interne comme `` présentes dans le corps du texte[cite: 10, 26, 44].
* [cite_start]**Format des liens** : Les URLs dans la section sources doivent impérativement être précédées d'un tiret et d'un espace (`- `) pour être correctement indexées[cite: 50, 71, 142].
* **Hiérarchie** : Une catégorie doit être déclarée au moins une fois avant les articles qui la composent. Le script conservera la dernière catégorie rencontrée pour tous les articles suivants jusqu'à la prochaine déclaration `**CATEGORIE :**`.
* **Séparateurs** : Vous pouvez utiliser des lignes de commentaires (ex: `##########`) pour structurer vos fichiers de travail ; le parser les ignorera tant qu'elles ne contiennent pas les mots-clés réservés.

## 🤝 Contribution

Les contributions doivent respecter les règles suivantes :
* Typage statique strict (`mypy`).
* Linting (`ruff` ou `flake8`).
* Utilisation des f-strings et dataclasses.

---
*Projet interne - Wavestone AI Practice.*