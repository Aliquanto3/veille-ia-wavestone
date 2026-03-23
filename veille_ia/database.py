"""Couche de persistance SQLite pour les news de veille IA."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Tuple

from veille_ia.config import DB_DEFAULT_PATH
from veille_ia.models import NewsItem

logger = logging.getLogger(__name__)


class NewsDatabase:
    """Gestion de la persistance des news dans SQLite.

    Schéma de la table ``news`` :

    ============== ======= ===============================================
    Colonne        Type    Description
    ============== ======= ===============================================
    uid            TEXT    Clé primaire (générée par NewsItem)
    category       TEXT    Catégorie principale
    sub_category   TEXT    Sous-catégorie
    title          TEXT    Titre de l'actualité
    description    TEXT    Corps (peut contenir du HTML si enrichi)
    links          TEXT    URLs séparées par ``\\n``
    date           TEXT    Date YYYY-MM-DD (indexée)
    is_enhanced    INTEGER 1 si enrichi par LLM, 0 sinon
    source         TEXT    Identifiant de la source d'ingestion
    created_at     TEXT    Timestamp d'insertion
    updated_at     TEXT    Timestamp de dernière mise à jour
    ============== ======= ===============================================
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS news (
        uid TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        sub_category TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        links TEXT DEFAULT '',
        date TEXT,
        is_enhanced INTEGER DEFAULT 0,
        source TEXT DEFAULT 'manual',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_news_date ON news(date);
    CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);
    """

    # Migration pour les BDD créées avant l'ajout de la colonne source
    _MIGRATIONS = [
        "ALTER TABLE news ADD COLUMN source TEXT DEFAULT 'manual'",
    ]

    # Index créés après les migrations (dépendent de colonnes ajoutées)
    _POST_MIGRATION_INDEX = [
        "CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)",
    ]

    def __init__(self, db_path: Path = DB_DEFAULT_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._run_migrations()
        self._create_post_migration_indexes()

    def __enter__(self) -> NewsDatabase:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _init_schema(self) -> None:
        self.conn.executescript(self.SCHEMA)
        self.conn.commit()

    def _run_migrations(self) -> None:
        """Applique les migrations non-breaking (ALTER TABLE ADD COLUMN)."""
        for migration in self._MIGRATIONS:
            try:
                self.conn.execute(migration)
                self.conn.commit()
            except sqlite3.OperationalError:
                pass  # Colonne déjà existante

    def _create_post_migration_indexes(self) -> None:
        """Crée les index qui dépendent de colonnes ajoutées par migration."""
        for stmt in self._POST_MIGRATION_INDEX:
            self.conn.execute(stmt)
        self.conn.commit()

    def ingest(self, items: List[NewsItem], source: str = "manual") -> Tuple[int, int]:
        """Point d'entrée principal pour l'ingestion multi-sources.

        Tague chaque item avec l'identifiant de source avant upsert.
        Utiliser cette méthode plutôt que upsert_items() directement
        pour garantir le traçage de la provenance.

        Args:
            items: Liste de NewsItem à ingérer.
            source: Identifiant de la source (ex: "manual:excel", "rss:techcrunch").

        Returns:
            Tuple (insérés, mis à jour).
        """
        for item in items:
            item.source = source
        return self.upsert_items(items)

    def upsert_items(self, items: List[NewsItem]) -> Tuple[int, int]:
        """Insère ou met à jour des news. Retourne (insérés, mis à jour).

        Déduplication par titre + date : si une news existe déjà avec le même
        titre et la même date, ses champs sont mis à jour (pas de doublon).
        """
        inserted, updated = 0, 0
        for item in items:
            links_str = "\n".join(item.links)
            existing = self.conn.execute(
                "SELECT uid FROM news WHERE title = ? AND date = ?",
                (item.title, item.date),
            ).fetchone()

            if existing:
                self.conn.execute(
                    """UPDATE news SET category=?, sub_category=?, description=?,
                       links=?, is_enhanced=?, source=?, updated_at=datetime('now')
                       WHERE uid=?""",
                    (item.category, item.sub_category, item.description,
                     links_str, int(item.is_enhanced), item.source, existing["uid"]),
                )
                updated += 1
            else:
                self.conn.execute(
                    """INSERT INTO news (uid, category, sub_category, title, description,
                       links, date, is_enhanced, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item.uid, item.category, item.sub_category, item.title,
                     item.description, links_str, item.date, int(item.is_enhanced), item.source),
                )
                inserted += 1

        self.conn.commit()
        logger.info("💾 BDD : %d insérés, %d mis à jour.", inserted, updated)
        return inserted, updated

    def get_all_items(self) -> List[NewsItem]:
        """Charge toutes les news depuis la BDD."""
        rows = self.conn.execute(
            "SELECT * FROM news ORDER BY date DESC, category, sub_category"
        ).fetchall()
        return self._rows_to_items(rows)

    def get_items_by_date_range(self, date_start: str, date_end: str) -> List[NewsItem]:
        """Charge les news dans une plage de dates."""
        rows = self.conn.execute(
            "SELECT * FROM news WHERE date >= ? AND date <= ? ORDER BY date DESC, category, sub_category",
            (date_start, date_end),
        ).fetchall()
        return self._rows_to_items(rows)

    def get_date_range(self) -> Tuple[Optional[str], Optional[str]]:
        """Retourne la plage de dates min/max en BDD."""
        row = self.conn.execute(
            "SELECT MIN(date) as min_date, MAX(date) as max_date FROM news WHERE date IS NOT NULL"
        ).fetchone()
        if row and row["min_date"]:
            return row["min_date"], row["max_date"]
        return None, None

    def count(self) -> int:
        """Nombre total de news en base."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM news").fetchone()
        return row["cnt"] if row else 0

    def _rows_to_items(self, rows: list) -> List[NewsItem]:
        """Convertit des lignes SQLite en NewsItem."""
        items: List[NewsItem] = []
        for row in rows:
            links = [lnk for lnk in row["links"].split("\n") if lnk.strip()] if row["links"] else []
            item = NewsItem(
                category=row["category"],
                sub_category=row["sub_category"],
                title=row["title"],
                description=row["description"],
                links=links,
                date=row["date"],
                source=row["source"] if "source" in row.keys() else "manual",
            )
            item.is_enhanced = bool(row["is_enhanced"])
            items.append(item)
        return items

    def close(self) -> None:
        self.conn.close()
