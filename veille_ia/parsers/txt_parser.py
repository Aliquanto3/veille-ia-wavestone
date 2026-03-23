"""Parser pour les fichiers texte de veille IA (format Markdown-like)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from veille_ia.models import NewsItem


class NewsParser:
    """Gère l'extraction depuis les fichiers textes."""

    RX_CATEGORY = re.compile(r"\*\*CATEGORIE\s*:\*\*\s*(.+)")
    RX_SUB_CATEGORY = re.compile(r"\*\*SOUS-CATEGORIE\s*:\*\*\s*(.+)")
    RX_TITLE = re.compile(r"\*\*TITRE\s*:\*\*\s*(.+)")
    RX_DESCRIPTION = re.compile(r"\*\*DESCRIPTION\s*:\*\*\s*(.*)")
    RX_SOURCES_HEADER = re.compile(r"\*\*SOURCES\s*:?\*\*")
    RX_LINK = re.compile(r"-\s*(https?://\S+)")

    @staticmethod
    def clean_text(text: str) -> str:
        return text.strip()

    def _flush_item(
        self,
        cat: Optional[str],
        sub: Optional[str],
        title: Optional[str],
        desc: List[str],
        links: List[str],
    ) -> Optional[NewsItem]:
        """Crée un NewsItem si les données minimales sont présentes."""
        if title and cat:
            return NewsItem(
                category=self.clean_text(cat),
                sub_category=self.clean_text(sub) if sub else "Général",
                title=self.clean_text(title),
                description=self.clean_text(" ".join(desc)),
                links=links,
            )
        return None

    def parse_file(self, file_path: Path) -> List[NewsItem]:
        """Parse un fichier .txt et retourne une liste de NewsItem."""
        if not file_path.exists():
            return []

        with open(file_path, "r", encoding="utf-8") as f:
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
            if not line:
                continue

            cat_match = self.RX_CATEGORY.match(line)
            sub_match = self.RX_SUB_CATEGORY.match(line)
            title_match = self.RX_TITLE.match(line)
            source_header_match = self.RX_SOURCES_HEADER.match(line)

            if cat_match:
                flushed = self._flush_item(current_cat, current_sub, current_title, current_desc, current_links)
                if flushed:
                    items.append(flushed)
                current_cat = cat_match.group(1)
                current_sub = None
                current_title = None
                current_desc = []
                current_links = []
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
                if not (line.startswith("**") or line.startswith("######")):
                    current_desc.append(line)

            if state == "READING_SOURCES":
                link_match = self.RX_LINK.match(line)
                if link_match:
                    current_links.append(link_match.group(1))

        flushed = self._flush_item(current_cat, current_sub, current_title, current_desc, current_links)
        if flushed:
            items.append(flushed)

        return items
