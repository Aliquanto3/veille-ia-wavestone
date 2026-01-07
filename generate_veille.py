"""
Générateur de Dashboard de Veille IA - Wavestone (Version CLI & Industrialisée).
Author: Senior AI Consultant & Assistant
Date: 2025-12-17
Description: Pipeline complet avec arguments CLI pour contrôle fin.
Compatibility: Python 3.10+, Mypy Strict, Ruff.
"""

import re
import os
import json
import html
import time
import argparse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Set, Any, Tuple
from urllib.parse import urlparse
from dotenv import load_dotenv

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None

# --- 1. Data Models ---

@dataclass
class NewsItem:
    """Représente une actualité unitaire."""
    category: str
    sub_category: str
    title: str
    description: str
    links: List[str] = field(default_factory=list)
    uid: str = field(init=False)
    is_enhanced: bool = False

    def __post_init__(self) -> None:
        clean_title = re.sub(r'\W+', '', self.title)
        self.uid = f"{clean_title[:15]}_{datetime.now().microsecond}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# --- 2. Parsing Logic (Ingestion) ---

class NewsParser:
    """Gère l'extraction depuis les fichiers textes."""

    RX_CATEGORY = re.compile(r'\*\*CATEGORIE\s*:\*\*\s*(.+)')
    RX_SUB_CATEGORY = re.compile(r'\*\*SOUS-CATEGORIE\s*:\*\*\s*(.+)')
    RX_TITLE = re.compile(r'\*\*TITRE\s*:\*\*\s*(.+)')
    RX_DESCRIPTION = re.compile(r'\*\*DESCRIPTION\s*:\*\*\s*(.*)')
    RX_SOURCES_HEADER = re.compile(r'\*\*SOURCES\s*:?\*\*')
    RX_LINK = re.compile(r'-\s*(https?://\S+)')

    @staticmethod
    def clean_text(text: str) -> str:
        return text.strip()

    def parse_file(self, file_path: Path) -> List[NewsItem]:
        if not file_path.exists():
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        items: List[NewsItem] = []
        current_cat: Optional[str] = None
        current_sub: Optional[str] = None
        current_title: Optional[str] = None
        current_desc: List[str] = []
        current_links: List[str] = []
        state = "SEARCHING"

        for line in lines:
            line = line.strip()
            if not line: continue

            cat_match = self.RX_CATEGORY.match(line)
            sub_match = self.RX_SUB_CATEGORY.match(line)
            title_match = self.RX_TITLE.match(line)
            source_header_match = self.RX_SOURCES_HEADER.match(line)

            if cat_match:
                if current_title and current_cat:
                    items.append(NewsItem(
                        category=self.clean_text(current_cat),
                        sub_category=self.clean_text(current_sub) if current_sub else "Général",
                        title=self.clean_text(current_title),
                        description=self.clean_text(" ".join(current_desc)),
                        links=current_links
                    ))
                    current_sub = None
                    current_title = None
                    current_desc = []
                    current_links = []
                current_cat = cat_match.group(1)
                state = "SEARCHING"
                continue

            if sub_match:
                current_sub = sub_match.group(1)
                continue

            if title_match:
                current_title = title_match.group(1)
                state = "SEARCHING"
                continue

            if line.startswith("**DESCRIPTION"):
                desc_match = self.RX_DESCRIPTION.match(line)
                if desc_match and desc_match.group(1):
                    current_desc.append(desc_match.group(1))
                state = "READING_DESC"
                continue

            if source_header_match:
                state = "READING_SOURCES"
                continue

            if state == "READING_DESC":
                if line.startswith("**") or line.startswith("######"): pass 
                else: current_desc.append(line)

            if state == "READING_SOURCES":
                link_match = self.RX_LINK.match(line)
                if link_match: current_links.append(link_match.group(1))

        if current_title and current_cat:
            items.append(NewsItem(
                category=self.clean_text(current_cat),
                sub_category=self.clean_text(current_sub) if current_sub else "Général",
                title=self.clean_text(current_title),
                description=self.clean_text(" ".join(current_desc)),
                links=current_links
            ))

        return items

# --- 3. Cognitive Layer (Mistral AI) ---

class MistralEnhancer:
    def __init__(self, api_key: str, model: str = "mistral-large-latest", batch_size: int = 10):
        if not Mistral:
            raise ImportError("Le module 'mistralai' n'est pas installé.")
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.batch_size = batch_size

    def enhance_items(self, items: List[NewsItem]) -> List[NewsItem]:
        total_items = len(items)
        print(f"\n🧠 Démarrage de l'enrichissement via Mistral (Mode Batch : {self.batch_size} items/appel)...")
        enhanced_results: List[NewsItem] = []

        for i in range(0, total_items, self.batch_size):
            chunk = items[i : i + self.batch_size]
            print(f"   📦 Traitement du lot {i//self.batch_size + 1}...")
            try:
                processed_chunk = self._process_batch(chunk)
                enhanced_results.extend(processed_chunk)
            except Exception as e:
                print(f"   ⚠️ Erreur critique sur le lot: {e}. Fallback sur originaux.")
                enhanced_results.extend(chunk)
            time.sleep(1)

        return enhanced_results

    def _process_batch(self, batch: List[NewsItem]) -> List[NewsItem]:
        input_data = [
            {
                "id": item.uid,
                "category": item.category,
                "sub_category": item.sub_category,
                "title": item.title,
                "description": item.description
            } 
            for item in batch
        ]

        prompt = f"""
        Tu es un expert en veille technologique et éditeur en chef chez Wavestone.
        Tu vas recevoir une liste d'actualités brutes au format JSON.
        
        Listes de référence (Vocabulaire Contrôlé) :
        - CATEGORIES : ["Marché", "Tech", "Gouvernance"]
        - SOUS-CATEGORIES : ["Souveraineté", "M&A", "Conseil", "Stratégie", "Economie", "Modèles", "Providers", "Développement", "Robotique", "Evaluation", "RSE", "Cybersécurité", "Conformité", "RH"]

        Ta mission pour CHAQUE actualité :
        
        1. **CLASSIFICATION (RÈGLE DE PRÉSERVATION)** :
           - Vérifie les champs 'category' et 'sub_category' reçus en input.
           - **SI** la valeur reçue existe DÉJÀ dans les listes de référence ci-dessus : **TU NE DOIS PAS LA CHANGER**. Garde-la strictement identique (même si tu penses qu'une autre serait mieux).
           - **SINON** (si le champ est vide ou contient une valeur inconnue) : Déduis la bonne valeur à partir du titre et de la description en piochant obligatoirement dans les listes.
        
        2. **ÉDITION** :
           - Corrige l'orthographe et le style du titre et de la description.
           - Ajoute 1 emoji pertinent au tout début du titre.
           - NE METS PAS de gras dans le TITRE.
           - Utilise les balises HTML <b>, <i> pour mettre en valeur les mots-clés dans la DESCRIPTION uniquement.

        Format de réponse attendu (JSON Strict) :
        {{
            "items": [
                {{
                    "id": "ID_ORIGINAL_OBLIGATOIRE",
                    "category": "Valeur conservée (si valide) ou corrigée",
                    "sub_category": "Valeur conservée (si valide) ou corrigée",
                    "title": "Emoji + Titre corrigé",
                    "description": "Description améliorée..."
                }}
            ]
        }}

        Données Input :
        {json.dumps(input_data, ensure_ascii=False)}
        """

        response = self.client.chat.complete(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        try:
            content = response.choices[0].message.content
            json_response = json.loads(content)
            output_items_dict = {item['id']: item for item in json_response.get('items', [])}
            
            result_batch = []
            for original_item in batch:
                enhanced_data = output_items_dict.get(original_item.uid)
                if enhanced_data:
                    original_item.title = enhanced_data.get('title', original_item.title)
                    original_item.description = enhanced_data.get('description', original_item.description)
                    original_item.category = enhanced_data.get('category', original_item.category)
                    original_item.sub_category = enhanced_data.get('sub_category', original_item.sub_category)
                    original_item.is_enhanced = True
                result_batch.append(original_item)
            return result_batch
        except Exception as e:
            print(f"      -> Erreur parsing JSON: {e}")
            return batch
        
    def generate_teams_report(self, items: List[NewsItem], date_range: str) -> str:
        """
        Génère une synthèse globale de la veille pour diffusion sur Microsoft Teams.
        Traite uniquement les titres et catégories pour optimiser la consommation de tokens.
        """
        print("📢 Génération du message de teasing Teams...")
        
        # On ne transmet que l'essentiel pour la synthèse globale
        summary_data = [
            {"cat": item.category, "sub": item.sub_category, "title": item.title}
            for item in items
        ]

        prompt = f"""
        Tu es Senior AI Consultant chez Wavestone. 
        Tu dois rédiger un message d'annonce percutant pour le canal Microsoft Teams de la practice IA.
        
        Données de la veille (Période : {date_range}) :
        {json.dumps(summary_data, ensure_ascii=False)}

        Consignes de rédaction :
        1. Ton : Professionnel, expert, engageant (Senior Consultant style).
        2. Structure :
           - Accroche courte avec emojis.
           - Section "À la une cette semaine" : Identifie les 3 actualités les plus stratégiques (toutes catégories confondues) et résume-les en une phrase percutante chacune.
           - Un appel à l'action invitant à consulter le Dashboard complet.
        3. Formatage : Utilise le Markdown compatible Teams (gras pour les noms d'entreprises ou technos).
        
        Réponds uniquement avec le texte du message, sans fioritures.
        """

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération du message Teams : {e}")
            return "La veille IA de la semaine est disponible sur le portail ! 🚀"

# --- 4. HTML Rendering Logic ---

class HTMLRenderer:
    def __init__(self, title: str, subtitle: str, date_range: str):
        self.title = title
        self.subtitle = subtitle
        self.date_range = date_range

    def _get_css(self) -> str:
        return """
        <style>
            :root {
                --ws-purple-main: #451DC7; --ws-purple-dark: #250F6B; --ws-green-bright: #04F06A; 
                --ws-green-light: #CAFEE0; --ws-black: #000000; --ws-white: #FFFFFF; --ws-gray-bg: #F4F6F8;
                --primary: var(--ws-purple-main); --secondary: var(--ws-purple-dark); --accent: var(--ws-green-bright);
                --highlight: var(--ws-green-light); --bg: var(--ws-gray-bg); --card-bg: var(--ws-white); --text: #333333;
                --border-radius: 8px;
            }
            body { font-family: 'Aptos', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; line-height: 1.5; font-size: 14px; }
            .container { max-width: 1600px; margin: 0 auto; }
            header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 3px solid var(--primary); padding-bottom: 15px; }
            h1 { color: var(--primary); font-size: 2rem; margin: 0; font-weight: 600; }
            .meta { color: var(--secondary); font-size: 0.9rem; margin-top: 5px; display: block; font-weight: 500; }
            .date-badge { display: inline-block; background: var(--ws-green-light); color: var(--ws-purple-dark); padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; margin-top: 5px; }
            
            /* Filters */
            .filters-panel { background: var(--card-bg); padding: 10px 20px; border-radius: var(--border-radius); box-shadow: 0 2px 10px rgba(69, 29, 199, 0.05); margin-bottom: 25px; border-left: 5px solid var(--secondary); }
            .filters-header { cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-weight: 600; color: var(--primary); font-size: 1.1rem; }
            .filters-header::after { content: '▼'; font-size: 0.8rem; margin-left: 10px; transition: transform 0.3s; color: var(--accent); }
            .filters-panel.open .filters-header::after { transform: rotate(180deg); }
            .filters-body { display: none; margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }
            .filters-panel.open .filters-body { display: block; animation: slideDown 0.3s ease-out; }
            .filters-grid { display: flex; gap: 20px; }
            .filter-col { flex: 1; background: var(--bg); padding: 15px; border-radius: 4px; }
            .filter-col h4 { margin: 0 0 15px 0; font-size: 1rem; color: var(--secondary); border-bottom: 2px solid var(--ws-green-light); padding-bottom: 5px; }
            .checkbox-group { display: flex; flex-direction: column; gap: 8px; }
            .checkbox-label { display: flex; align-items: center; cursor: pointer; font-size: 0.9rem; color: #444; transition: color 0.2s; }
            .checkbox-label:hover { color: var(--primary); }
            .checkbox-label input { accent-color: var(--primary); margin-right: 10px; }
            .checkbox-label.checked { font-weight: bold; color: var(--primary); }

            /* Search */
            .search-box { flex-grow: 1; min-width: 250px; max-width: 450px; margin-left: 20px;}
            .search-box input { width: 100%; padding: 10px 15px; border: 2px solid #ddd; border-radius: 20px; font-family: inherit; transition: border-color 0.2s; box-sizing: border-box; }
            .search-box input:focus { outline: none; border-color: var(--primary); }

            /* Columns & Cards */
            .columns-container { display: flex; gap: 25px; overflow-x: auto; align-items: flex-start; padding-bottom: 20px; }
            .column { flex: 1; min-width: 320px; background: #EAECEF; border-radius: var(--border-radius); padding: 15px; display: flex; flex-direction: column; gap: 15px; border-top: 5px solid var(--secondary); }
            .col-header { font-size: 1.2rem; font-weight: 700; text-align: center; color: var(--primary); padding-bottom: 10px; border-bottom: 1px solid rgba(0,0,0,0.1); text-transform: uppercase; letter-spacing: 0.5px; }
            .sub-group { margin-bottom: 10px; }
            .sub-header { font-size: 0.85rem; font-weight: 700; color: var(--secondary); margin: 15px 0 8px 0; text-transform: uppercase; display: flex; align-items: center; }
            .sub-header::before { content: ''; display: inline-block; width: 8px; height: 8px; background-color: var(--accent); border-radius: 50%; margin-right: 8px; }
            .news-item { background: var(--card-bg); border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); overflow: hidden; margin-bottom: 10px; transition: all 0.2s; border-left: 4px solid transparent; }
            .news-item:hover { box-shadow: 0 4px 12px rgba(69, 29, 199, 0.15); transform: translateY(-2px); }
            .news-title { padding: 12px 15px; cursor: pointer; font-weight: 600; color: var(--text); display: flex; justify-content: space-between; align-items: center; line-height: 1.4; }
            .news-title span { display: block; padding-right: 10px; }
            .news-title::after { content: '+'; font-size: 1.4rem; color: var(--secondary); font-weight: 300; flex-shrink: 0; }
            .news-item.active { border-left-color: var(--accent); }
            .news-item.active .news-title { background-color: var(--highlight); color: var(--ws-black); }
            .news-item.active .news-title::after { content: '−'; color: var(--primary); }
            .news-content { display: none; padding: 15px; border-top: 1px solid var(--ws-green-light); font-size: 0.95rem; color: #333; background: #fff; }
            .news-item.active .news-content { display: block; }
            .news-content b { color: var(--secondary); }
            .news-description-text { margin-bottom: 10px; }

            /* Links & Actions */
            .links { margin-top: 15px; padding-top: 10px; border-top: 1px dashed #ddd; font-size: 0.85rem; }
            .links ul { list-style-type: none; padding-left: 0; margin-bottom: 10px; }
            .links li { margin-bottom: 5px; display: flex; align-items: center; }
            .links a { color: #4682b4; text-decoration: none; font-weight: 500; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; max-width: 250px; display: inline-block; vertical-align: middle;}
            .links a:hover { text-decoration: underline; color: var(--primary); }
            .actions { display: flex; justify-content: flex-end; margin-top: 10px; }
            .copy-btn { background-color: transparent; color: var(--primary); border: 1px solid var(--primary); padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; font-weight: 600; transition: all 0.2s; display: flex; align-items: center; gap: 5px; }
            .copy-btn:hover { background-color: var(--primary); color: white; }
            .copy-btn:active { transform: scale(0.95); }
            
            @media (max-width: 768px) { 
                .columns-container, .filters-grid { flex-direction: column; } 
                header { flex-direction: column; align-items: flex-start; gap: 15px; }
                .search-box { margin-left: 0; width: 100%; max-width: 100%; }
            }
            @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        </style>
        """

    def _get_js(self) -> str:
        return """
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const filterHeader = document.querySelector('.filters-header');
                const filterPanel = document.querySelector('.filters-panel');
                if(filterHeader) filterHeader.addEventListener('click', () => { filterPanel.classList.toggle('open'); });

                document.querySelectorAll('.news-title').forEach(header => {
                    header.addEventListener('click', () => { header.parentElement.classList.toggle('active'); });
                });

                document.querySelectorAll('.copy-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const item = btn.closest('.news-item');
                        const title = item.querySelector('.news-title span').innerText;
                        const desc = item.querySelector('.news-description-text').innerText.trim();
                        const links = [];
                        item.querySelectorAll('.links a').forEach(a => links.push(a.href));
                        
                        let textToCopy = `**${title}**\\n\\n${desc}`;
                        if(links.length > 0) textToCopy += `\\n\\n**Sources :**\\n` + links.map(l => `- ${l}`).join('\\n');

                        navigator.clipboard.writeText(textToCopy).then(() => {
                            const originalText = btn.innerText;
                            btn.innerText = "✅ Copié !";
                            btn.style.backgroundColor = "var(--accent)";
                            btn.style.borderColor = "var(--accent)";
                            btn.style.color = "black";
                            setTimeout(() => {
                                btn.innerText = originalText;
                                btn.style.backgroundColor = ""; btn.style.borderColor = ""; btn.style.color = "";
                            }, 2000);
                        }).catch(err => { alert("Erreur copie."); });
                    });
                });

                const searchInput = document.getElementById('searchInput');
                const catCheckboxes = document.querySelectorAll('.cat-cb');
                const subCheckboxes = document.querySelectorAll('.sub-cb');
                const columns = document.querySelectorAll('.column');
                const items = document.querySelectorAll('.news-item');

                function updateFilters() {
                    const searchTerm = searchInput.value.toLowerCase();
                    const selectedCats = Array.from(catCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
                    const selectedSubs = Array.from(subCheckboxes).filter(cb => cb.checked).map(cb => cb.value);

                    columns.forEach(col => {
                        const cat = col.dataset.cat;
                        if (selectedCats.length === 0 || selectedCats.includes(cat)) col.style.display = 'flex';
                        else col.style.display = 'none';
                    });

                    items.forEach(item => {
                        const title = item.querySelector('.news-title').innerText.toLowerCase();
                        const desc = item.querySelector('.news-content').innerText.toLowerCase();
                        const itemCat = item.dataset.cat;
                        const itemSub = item.dataset.sub;
                        const matchesSearch = title.includes(searchTerm) || desc.includes(searchTerm);
                        const matchesCat = selectedCats.length === 0 || selectedCats.includes(itemCat);
                        const matchesSub = selectedSubs.length === 0 || selectedSubs.includes(itemSub);
                        item.style.display = (matchesSearch && matchesCat && matchesSub) ? 'block' : 'none';
                    });
                    
                    document.querySelectorAll('.sub-group').forEach(group => {
                        const visibleChildren = Array.from(group.querySelectorAll('.news-item')).filter(i => i.style.display !== 'none');
                        const header = group.querySelector('.sub-header');
                        if (header) header.style.display = visibleChildren.length > 0 ? 'flex' : 'none';
                    });
                }

                document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.addEventListener('change', (e) => {
                        const label = e.target.parentElement;
                        if(e.target.checked) label.classList.add('checked');
                        else label.classList.remove('checked');
                        updateFilters();
                    });
                });
                searchInput.addEventListener('input', updateFilters);
            });
        </script>
        """

    def render(self, items: List[NewsItem]) -> str:
        data_tree: Dict[str, Dict[str, List[NewsItem]]] = {}
        all_cats: Set[str] = set()

        for item in items:
            all_cats.add(item.category)
            if item.category not in data_tree: data_tree[item.category] = {}
            if item.sub_category not in data_tree[item.category]: data_tree[item.category][item.sub_category] = []
            data_tree[item.category][item.sub_category].append(item)

        sorted_cats = sorted(list(all_cats))
        columns_html = ""

        for cat in sorted_cats:
            sub_groups_html = ""
            cat_subs = sorted(data_tree[cat].keys())
            for sub in cat_subs:
                items_in_sub = data_tree[cat][sub]
                items_html = ""
                for item in items_in_sub:
                    if item.is_enhanced:
                        safe_title = item.title 
                        safe_desc = item.description.replace('\n', '<br>')
                    else:
                        safe_title = html.escape(item.title)
                        safe_desc = html.escape(item.description).replace('\n', '<br>')
                    
                    safe_links = ""
                    if item.links:
                        links_li = ""
                        for l in item.links:
                            try:
                                parsed = urlparse(l)
                                domain = parsed.netloc.replace('www.', '')
                                if not domain: domain = "Lien source"
                            except: domain = "Lien source"
                            links_li += f'<li>🔗 <a href="{l}" target="_blank" title="{l}">{domain}</a></li>'
                        safe_links = f'<div class="links"><ul>{links_li}</ul></div>'

                    actions_html = """<div class="actions"><button class="copy-btn">📋 Copier pour Teams</button></div>"""
                    items_html += f"""
                    <div class="news-item" data-cat="{cat}" data-sub="{sub}">
                        <div class="news-title"><span>{safe_title}</span></div>
                        <div class="news-content">
                            <div class="news-description-text">{safe_desc}</div>
                            {safe_links}{actions_html}
                        </div>
                    </div>"""
                sub_groups_html += f"""<div class="sub-group"><div class="sub-header">{sub}</div>{items_html}</div>"""
            columns_html += f"""<div class="column" data-cat="{cat}"><div class="col-header">{cat}</div>{sub_groups_html}</div>"""

        filter_columns_html = ""
        for cat in sorted_cats:
            cat_subs = sorted(data_tree[cat].keys())
            subs_checkboxes = ""
            for sub in cat_subs:
                subs_checkboxes += f"""<label class="checkbox-label"><input type="checkbox" class="sub-cb" value="{sub}"> {sub}</label>"""
            filter_columns_html += f"""
            <div class="filter-col">
                <h4><label style="cursor:pointer;"><input type="checkbox" class="cat-cb" value="{cat}"> {cat}</label></h4>
                <div class="checkbox-group">{subs_checkboxes}</div>
            </div>"""

        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.title}</title>
            {self._get_css()}
        </head>
        <body>
            <div class="container">
                <header>
                    <div>
                        <h1>{self.title}</h1>
                        <span class="meta">{self.subtitle}</span>
                        <div class="date-badge">📅 Période : {self.date_range}</div>
                    </div>
                    <div class="search-box">
                        <input type="text" id="searchInput" placeholder="Rechercher une actualité...">
                    </div>
                </header>
                <div class="filters-panel">
                    <div class="filters-header"><span>🔍 Filtres avancés</span></div>
                    <div class="filters-body"><div class="filters-grid">{filter_columns_html}</div></div>
                </div>
                <div class="columns-container">{columns_html}</div>
            </div>
            {self._get_js()}
        </body>
        </html>
        """

# --- 5. Main Execution ---

def resolve_input_directory(base_input_dir: str, arg_start: str, arg_end: str) -> Tuple[Path, str, str]:
    """
    Détermine le dossier source et les dates.
    Priorité 1 : Dates fournies en argument (cherche le dossier correspondant).
    Priorité 2 : Le dossier le plus récent trouvé dans inputs/.
    """
    base_path = Path(base_input_dir)
    if not base_path.exists():
        base_path.mkdir(exist_ok=True) # Crée inputs/ si inexistant

    # Cas 1 : L'utilisateur force des dates via CLI
    if arg_start != "?" and arg_end != "?":
        # On suppose que l'utilisateur entre des dates au format du dossier ou DD/MM
        # Pour simplifier, on cherche si un dossier contient ces chaînes
        potential_dir_name = f"{arg_start}_{arg_end}" # Ex: 2025-12-19_2026-01-05
        target_path = base_path / potential_dir_name
        
        if target_path.exists():
            return target_path, arg_start, arg_end
        else:
            print(f"⚠️ Dossier spécifique '{potential_dir_name}' introuvable. Recherche automatique...")

    # Cas 2 : Recherche automatique du dossier le plus récent (format YYYY-MM-DD_YYYY-MM-DD)
    subdirs = [d for d in base_path.iterdir() if d.is_dir()]
    valid_dirs = []
    
    # Regex pour capturer les dates YYYY-MM-DD_YYYY-MM-DD
    dir_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})")

    for d in subdirs:
        match = dir_pattern.match(d.name)
        if match:
            start_date = match.group(1)
            end_date = match.group(2)
            valid_dirs.append((d, start_date, end_date))

    if not valid_dirs:
        # Fallback : on retourne à la racine inputs/ si pas de sous-dossiers datés
        print("ℹ️ Aucun sous-dossier daté trouvé. Utilisation de la racine 'inputs/'.")
        # Calcul par défaut (Lundi précédent) pour l'affichage
        today = datetime.now()
        curr = today - timedelta(days=today.weekday())
        prev = curr - timedelta(weeks=1)
        return base_path, prev.strftime("%Y-%m-%d"), curr.strftime("%Y-%m-%d")

    # Tri par date de fin (la plus récente en dernier)
    valid_dirs.sort(key=lambda x: x[2], reverse=True)
    
    best_dir, start, end = valid_dirs[0]
    return best_dir, start, end

def main() -> None:
    load_dotenv()

    # --- CLI Arguments ---
    parser = argparse.ArgumentParser(description="Générateur de Veille IA Wavestone")
    parser.add_argument("--no-mistral", action="store_true", help="Désactiver l'IA")
    parser.add_argument("--save-json", action="store_true", help="Debug JSON")
    parser.add_argument("-o", "--output", type=str, help="Fichier HTML sortie", default=None)
    parser.add_argument("--title", type=str, default="🤖 Veille IA Wavestone", help="Titre")
    parser.add_argument("--subtitle", type=str, default=None, help="Sous-titre")
    parser.add_argument("--date-start", type=str, default="?", help="Format YYYY-MM-DD")
    parser.add_argument("--date-end", type=str, default="?", help="Format YYYY-MM-DD")
    parser.add_argument("--input-dir", type=str, default="inputs", help="Dossier racine")
    
    args = parser.parse_args()

    # --- 0. CONFIGURATION DES SORTIES (NOUVEAU BLOC) ---
    # Création de l'arborescence outputs/
    base_output = Path("outputs")
    dir_pages = base_output / "pages"           # Pour les HTML
    dir_json = base_output / "TexteMistral"     # Pour les JSON
    dir_teams = base_output / "Teams"           # Pour les TXT

    # On crée tous les dossiers d'un coup (parents=True crée 'outputs' si besoin)
    for d in [dir_pages, dir_json, dir_teams]:
        d.mkdir(parents=True, exist_ok=True)

    # --- 1. Résolution du dossier source et des dates ---
    input_folder_root = args.input_dir
    target_folder, final_start_date, final_end_date = resolve_input_directory(
        input_folder_root, args.date_start, args.date_end
    )
    
    print(f"📂 Dossier source : {target_folder}")
    print(f"📅 Période détectée : {final_start_date} au {final_end_date}")

    # --- 2. Préparation des formats de dates ---
    try:
        d_s_obj = datetime.strptime(final_start_date, "%Y-%m-%d")
        d_e_obj = datetime.strptime(final_end_date, "%Y-%m-%d")
        display_date_range = f"Semaine du {d_s_obj.strftime('%d/%m')} au {d_e_obj.strftime('%d/%m')}"
        file_date_start = d_s_obj.strftime('%d-%m')
        file_date_end = d_e_obj.strftime('%d-%m')
    except ValueError:
        display_date_range = f"Période : {final_start_date} au {final_end_date}"
        file_date_start = final_start_date.replace('/', '-')
        file_date_end = final_end_date.replace('/', '-')

    # --- Configuration API ---
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not args.no_mistral and not api_key:
        print("⚠️  Pas de clé API. Mode --no-mistral forcé.")
        args.no_mistral = True

    # --- Parsing ---
    news_parser = NewsParser()
    all_items: List[NewsItem] = []

    if not target_folder.exists():
        print(f"❌ Erreur: Dossier '{target_folder}' introuvable.")
        return

    print(f"--- Démarrage de la Veille IA ---")
    txt_files = list(target_folder.glob("*.txt"))
    
    if not txt_files:
         print(f"⚠️ Aucun fichier .txt trouvé dans {target_folder}")
         return

    for file_path in txt_files:
        print(f"📖 Parsing de {file_path.name}...")
        items = news_parser.parse_file(file_path)
        all_items.extend(items)

    if not all_items:
        print("Aucun article trouvé.")
        return

    # --- Enhancement (Mistral) ---
    if not args.no_mistral:
        enhancer = MistralEnhancer(api_key=api_key)
        all_items = enhancer.enhance_items(all_items)
        
        teams_message = enhancer.generate_teams_report(all_items, display_date_range)
        
        # Sauvegarde TXT dans outputs/Teams
        teams_filename = f"Annonce_Teams_du_{file_date_start}_au_{file_date_end}.txt"
        teams_path = dir_teams / teams_filename
        
        with open(teams_path, "w", encoding="utf-8") as f:
            f.write(teams_message)
            
        # On garde une copie à la racine pour le bot GitHub Actions (facultatif mais pratique)
        with open("teams_announcement.txt", "w", encoding="utf-8") as f:
            f.write(teams_message)
        
        print(f"✅ Message Teams sauvegardé dans : {teams_path}")

    else:
        print("⏩ Mode No-Mistral actif : saut de l'étape d'enrichissement.")

    # --- Save JSON (Debug) ---
    if args.save_json:
        # Sauvegarde JSON dans outputs/TexteMistral
        json_filename = f"debug_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_path = dir_json / json_filename
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([item.to_dict() for item in all_items], f, indent=4, ensure_ascii=False)
        print(f"💾 Données JSON sauvegardées dans : {json_path}")

    # --- Rendering ---
    if args.subtitle:
        final_subtitle = args.subtitle
    else:
        final_subtitle = f"Généré le {datetime.now().strftime('%d/%m/%Y')} • {len(all_items)} actualités"
    
    renderer = HTMLRenderer(title=args.title, subtitle=final_subtitle, date_range=display_date_range)
    html_content = renderer.render(all_items)
    
    if args.output:
        output_filename = args.output
        if not output_filename.endswith('.html'): output_filename += ".html"
    else:
        output_filename = f"Veille_IA_{datetime.now().strftime('%Y-%m-%d')}.html"

    # Sauvegarde HTML dans outputs/pages
    final_output_path = dir_pages / output_filename

    with open(final_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n🚀 Succès ! Dashboard généré : {final_output_path}")

if __name__ == "__main__":
    main()