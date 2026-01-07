"""
Générateur de Portail (Index) pour Veille IA Wavestone.
Author: Senior AI Consultant & Assistant
Date: 2025-12-17
Description: Scanne les fichiers HTML de veille et génère une page d'accueil (index.html).
Compatibility: Python 3.10+
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

def get_veille_files(directory: Path) -> List[Tuple[str, str, datetime]]:
    """
    Scanne le répertoire pour trouver les fichiers HTML de veille.
    Retourne une liste de tuples (nom_fichier, titre_affichage, date_objet).
    """
    html_files = []
    # Regex pour capturer la date dans le nom de fichier (ex: Veille_IA_2026-01-06.html)
    # Adapte le pattern si tu changes tes noms de fichiers
    name_pattern = re.compile(r"Veille_IA_(\d{4}-\d{2}-\d{2})")

    for file_path in directory.glob("*.html"):
        filename = file_path.name
        
        # On ignore le fichier index.html lui-même pour ne pas se boucler
        if filename.lower() == "index.html":
            continue

        # Tentative d'extraction de la date via le nom de fichier
        match = name_pattern.search(filename)
        if match:
            date_str = match.group(1)
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_title = f"Veille du {date_obj.strftime('%d/%m/%Y')}"
            except ValueError:
                date_obj = datetime.fromtimestamp(file_path.stat().st_mtime)
                display_title = filename
        else:
            # Fallback : date de modification du fichier
            date_obj = datetime.fromtimestamp(file_path.stat().st_mtime)
            display_title = filename.replace(".html", "").replace("_", " ")

        html_files.append((filename, display_title, date_obj))

    # Tri par date décroissante (le plus récent en haut)
    html_files.sort(key=lambda x: x[2], reverse=True)
    return html_files

def generate_index_html(files: List[Tuple[str, str, datetime]]) -> str:
    """Génère le code HTML du portail."""
    
    links_html = ""
    for filename, title, date_obj in files:
        # Code couleur Wavestone pour les cartes
        links_html += f"""
        <a href="outputs/pages/{filename}" class="veille-card">
            <div class="card-icon">📅</div>
            <div class="card-content">
                <div class="card-title">{title}</div>
                <div class="card-date">Publié le {date_obj.strftime('%d/%m/%Y')}</div>
            </div>
            <div class="card-arrow">➔</div>
        </a>
        """

    if not files:
        links_html = "<div class='empty-state'>Aucune veille archivée pour le moment.</div>"

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portail Veille IA - Wavestone</title>
        <style>
            :root {{
                --ws-purple: #451DC7;
                --ws-dark: #250F6B;
                --ws-green: #04F06A;
                --bg: #F4F6F8;
                --text: #333;
            }}
            body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            
            header {{ text-align: center; margin-bottom: 50px; padding-top: 40px; }}
            h1 {{ color: var(--ws-purple); font-size: 2.5rem; margin-bottom: 10px; }}
            .subtitle {{ color: #666; font-size: 1.1rem; }}
            
            .grid {{ display: flex; flex-direction: column; gap: 15px; }}
            
            .veille-card {{ 
                display: flex; align-items: center; background: white; padding: 20px; 
                border-radius: 12px; text-decoration: none; color: inherit;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s;
                border-left: 5px solid var(--ws-purple);
            }}
            .veille-card:hover {{ transform: translateY(-3px); box-shadow: 0 5px 15px rgba(69, 29, 199, 0.15); }}
            
            .card-icon {{ font-size: 2rem; margin-right: 20px; }}
            .card-content {{ flex-grow: 1; }}
            .card-title {{ font-size: 1.2rem; font-weight: bold; color: var(--ws-dark); }}
            .card-date {{ color: #888; font-size: 0.9rem; margin-top: 4px; }}
            .card-arrow {{ color: var(--ws-purple); font-weight: bold; font-size: 1.2rem; }}
            
            footer {{ margin-top: 60px; text-align: center; color: #999; font-size: 0.8rem; border-top: 1px solid #ddd; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🤖 Veille IA Wavestone</h1>
                <div class="subtitle">Portail d'accès aux archives hebdomadaires</div>
            </header>
            
            <div class="grid">
                {links_html}
            </div>

            <footer>
                Wavestone AI Practice • Généré automatiquement
            </footer>
        </div>
    </body>
    </html>
    """

def main():
    # 1. CHANGEMENT DU DOSSIER CIBLE
    base_path = Path("outputs/pages")
    
    if not base_path.exists():
        print("⚠️ Le dossier 'outputs/pages' n'existe pas encore.")
        return

    # 2. Récupération des fichiers
    files = get_veille_files(base_path)
    print(f"🔎 {len(files)} archives trouvées dans outputs/pages/.")

    # 3. Génération de l'index
    html_content = generate_index_html(files)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("✅ Fichier 'index.html' mis à jour avec succès.")

if __name__ == "__main__":
    main()