"""Protocole et implémentations des sources de données."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Protocol, Tuple

from veille_ia.config import BASE_INPUT_DIR
from veille_ia.database import NewsDatabase
from veille_ia.models import NewsItem
from veille_ia.parsers.excel_reader import ExcelReader
from veille_ia.parsers.txt_parser import NewsParser
from veille_ia.utils import resolve_input_directory

logger = logging.getLogger(__name__)


class NewsSource(Protocol):
    """Interface commune pour toutes les sources de données."""

    def load(self) -> Tuple[List[NewsItem], str, str]:
        """Retourne (items, date_start, date_end)."""
        ...


class TxtSource:
    """Source de données : fichiers .txt dans un dossier daté."""

    def __init__(self, input_dir: str = BASE_INPUT_DIR, date_start: str = "?", date_end: str = "?"):
        self.input_dir = input_dir
        self.date_start = date_start
        self.date_end = date_end

    def load(self) -> Tuple[List[NewsItem], str, str]:
        target_folder, start, end = resolve_input_directory(
            self.input_dir, self.date_start, self.date_end
        )
        logger.info("📂 Dossier source : %s", target_folder)

        if not target_folder.exists():
            logger.error("❌ Dossier '%s' introuvable.", target_folder)
            return [], start, end

        parser = NewsParser()
        all_items: List[NewsItem] = []
        txt_files = list(target_folder.glob("*.txt"))

        if not txt_files:
            logger.warning("⚠️ Aucun fichier .txt trouvé dans %s", target_folder)
            return [], start, end

        for file_path in txt_files:
            logger.info("📖 Parsing de %s...", file_path.name)
            items = parser.parse_file(file_path)
            for item in items:
                item.source = "manual:txt"
            all_items.extend(items)

        return all_items, start, end


class ExcelSource:
    """Source de données : fichier Excel structuré."""

    def __init__(self, excel_path: Path, date_start: str = "?", date_end: str = "?"):
        self.excel_path = excel_path
        self.date_start = date_start
        self.date_end = date_end

    def load(self) -> Tuple[List[NewsItem], str, str]:
        logger.info("📊 Mode Excel : lecture depuis %s", self.excel_path)

        with ExcelReader(self.excel_path) as reader:
            categories, sub_categories = reader.read_vocabulary()
            logger.info("📋 Vocabulaire : %d catégories, %d sous-catégories", len(categories), len(sub_categories))
            items = reader.read_news()
            for item in items:
                item.source = "manual:excel"

        start, end = self._resolve_dates(items)
        return items, start, end

    def _resolve_dates(self, items: List[NewsItem]) -> Tuple[str, str]:
        if self.date_start != "?" and self.date_end != "?":
            return self.date_start, self.date_end
        dates = [item.date for item in items if item.date]
        if dates:
            return min(dates), max(dates)
        today = datetime.now().strftime("%Y-%m-%d")
        return today, today


class DbSource:
    """Source de données : base SQLite."""

    def __init__(self, db_path: Path, date_start: str = "?", date_end: str = "?"):
        self.db_path = db_path
        self.date_start = date_start
        self.date_end = date_end

    def load(self) -> Tuple[List[NewsItem], str, str]:
        logger.info("🗄️ Mode BDD : lecture depuis %s", self.db_path)

        with NewsDatabase(self.db_path) as db:
            if self.date_start != "?" and self.date_end != "?":
                items = db.get_items_by_date_range(self.date_start, self.date_end)
                start, end = self.date_start, self.date_end
            else:
                items = db.get_all_items()
                min_d, max_d = db.get_date_range()
                start = min_d or datetime.now().strftime("%Y-%m-%d")
                end = max_d or datetime.now().strftime("%Y-%m-%d")

            logger.info("🗄️ %d news chargées (%d total en base).", len(items), db.count())

        return items, start, end
