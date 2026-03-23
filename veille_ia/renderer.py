"""Moteur de rendu HTML pour le dashboard de veille IA."""

from __future__ import annotations

import html
import re
from typing import Dict, List, Set
from urllib.parse import urlparse

from veille_ia.config import ASSETS_DIR
from veille_ia.models import NewsItem

_ALLOWED_TAGS_RE = re.compile(r"</?[bi]>")


def sanitize_html(text: str, allow_tags: bool = False) -> str:
    """Échappe le HTML. Si allow_tags=True, préserve <b>, <i>, </b>, </i>."""
    if not allow_tags:
        return html.escape(text)
    placeholders: Dict[str, str] = {}
    for i, tag in enumerate(_ALLOWED_TAGS_RE.findall(text)):
        placeholder = f"__TAG{i}__"
        placeholders[placeholder] = tag
        text = text.replace(tag, placeholder, 1)
    text = html.escape(text)
    for placeholder, tag in placeholders.items():
        text = text.replace(html.escape(placeholder), tag)
    return text


class HTMLRenderer:
    """Génère le dashboard HTML complet à partir d'une liste de NewsItem."""

    def __init__(self, title: str, subtitle: str, date_range: str):
        self.title = title
        self.subtitle = subtitle
        self.date_range = date_range

    def _load_asset(self, filename: str) -> str:
        """Charge un fichier asset (CSS ou JS) depuis le dossier assets/."""
        asset_path = ASSETS_DIR / filename
        if asset_path.exists():
            return asset_path.read_text(encoding="utf-8")
        return ""

    def _get_css(self) -> str:
        return f"<style>{self._load_asset('style.css')}</style>"

    def _get_js(self) -> str:
        return f"<script>{self._load_asset('script.js')}</script>"

    def render(self, items: List[NewsItem]) -> str:
        """Génère le HTML complet du dashboard."""
        data_tree, sorted_cats = self._build_data_tree(items)
        columns_html = self._render_columns(data_tree, sorted_cats)
        filter_columns_html = self._render_filters(data_tree, sorted_cats)

        return f"""<!DOCTYPE html>
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
            <div class="filters-body">
                <div class="date-filters">
                    <label>Du</label>
                    <input type="date" id="dateStart">
                    <label>Au</label>
                    <input type="date" id="dateEnd">
                    <button class="reset-dates" id="resetDates">Réinitialiser</button>
                </div>
                <div class="filters-grid">{filter_columns_html}</div>
            </div>
        </div>
        <div class="columns-container">{columns_html}</div>
    </div>
    {self._get_js()}
</body>
</html>"""

    @staticmethod
    def _build_data_tree(items: List[NewsItem]) -> tuple:
        """Organise les items en arbre catégorie → sous-catégorie → items."""
        data_tree: Dict[str, Dict[str, List[NewsItem]]] = {}
        all_cats: Set[str] = set()
        for item in items:
            all_cats.add(item.category)
            if item.category not in data_tree:
                data_tree[item.category] = {}
            if item.sub_category not in data_tree[item.category]:
                data_tree[item.category][item.sub_category] = []
            data_tree[item.category][item.sub_category].append(item)
        return data_tree, sorted(list(all_cats))

    def _render_columns(self, data_tree: Dict, sorted_cats: List[str]) -> str:
        """Génère le HTML des colonnes Kanban."""
        columns_html = ""
        for cat in sorted_cats:
            safe_cat = html.escape(cat, quote=True)
            sub_groups_html = ""
            for sub in sorted(data_tree[cat].keys()):
                safe_sub = html.escape(sub, quote=True)
                items_html = ""
                for item in data_tree[cat][sub]:
                    items_html += self._render_card(item, safe_cat, safe_sub)
                sub_groups_html += f'<div class="sub-group"><div class="sub-header">{html.escape(sub)}</div>{items_html}</div>'
            columns_html += f'<div class="column" data-cat="{safe_cat}"><div class="col-header">{html.escape(cat)}</div>{sub_groups_html}</div>'
        return columns_html

    @staticmethod
    def _render_card(item: NewsItem, safe_cat: str, safe_sub: str) -> str:
        """Génère le HTML d'une carte news."""
        safe_title = sanitize_html(item.title, allow_tags=False)
        safe_desc = sanitize_html(item.description, allow_tags=item.is_enhanced).replace("\n", "<br>")
        safe_date = html.escape(item.date, quote=True) if item.date else ""
        date_badge = f'<div class="news-date-badge">📅 {html.escape(item.date)}</div>' if item.date else ""

        safe_links = ""
        if item.links:
            links_li = ""
            for link in item.links:
                try:
                    domain = urlparse(link).netloc.replace("www.", "") or "Lien source"
                except (ValueError, AttributeError):
                    domain = "Lien source"
                safe_url = html.escape(link, quote=True)
                links_li += f'<li>🔗 <a href="{safe_url}" target="_blank" title="{safe_url}">{html.escape(domain)}</a></li>'
            safe_links = f'<div class="links"><ul>{links_li}</ul></div>'

        return f"""
        <div class="news-item" data-cat="{safe_cat}" data-sub="{safe_sub}" data-date="{safe_date}">
            <div class="news-title"><span>{safe_title}</span></div>
            <div class="news-content">
                {date_badge}
                <div class="news-description-text">{safe_desc}</div>
                {safe_links}
                <div class="actions"><button class="copy-btn">📋 Copier pour Teams</button></div>
            </div>
        </div>"""

    @staticmethod
    def _render_filters(data_tree: Dict, sorted_cats: List[str]) -> str:
        """Génère le HTML des filtres par catégorie/sous-catégorie."""
        filter_html = ""
        for cat in sorted_cats:
            safe_cat = html.escape(cat, quote=True)
            subs_html = ""
            for sub in sorted(data_tree[cat].keys()):
                safe_sub = html.escape(sub, quote=True)
                subs_html += f'<label class="checkbox-label"><input type="checkbox" class="sub-cb" value="{safe_sub}"> {html.escape(sub)}</label>'
            filter_html += f"""
            <div class="filter-col">
                <h4><label style="cursor:pointer;"><input type="checkbox" class="cat-cb" value="{safe_cat}"> {html.escape(cat)}</label></h4>
                <div class="checkbox-group">{subs_html}</div>
            </div>"""
        return filter_html
