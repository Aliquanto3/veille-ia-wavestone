"""Tests pour veille_ia.database."""

from pathlib import Path

import pytest

from veille_ia.database import NewsDatabase
from veille_ia.models import NewsItem


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


class TestNewsDatabase:
    def test_insert_and_count(self, tmp_db: Path, sample_items: list[NewsItem]):
        """Insert N items → count = N."""
        with NewsDatabase(tmp_db) as db:
            ins, upd = db.upsert_items(sample_items)
            assert ins == 3
            assert upd == 0
            assert db.count() == 3

    def test_upsert_dedup(self, tmp_db: Path, sample_items: list[NewsItem]):
        """Un item avec même titre+date est mis à jour, pas dupliqué."""
        with NewsDatabase(tmp_db) as db:
            db.upsert_items(sample_items)
            # Modifier et ré-insérer
            sample_items[0].description = "UPDATED"
            ins, upd = db.upsert_items([sample_items[0]])
            assert ins == 0
            assert upd == 1
            assert db.count() == 3

    def test_get_by_date_range(self, tmp_db: Path, sample_items: list[NewsItem]):
        """Filtrage par plage de dates."""
        with NewsDatabase(tmp_db) as db:
            db.upsert_items(sample_items)
            filtered = db.get_items_by_date_range("2025-12-19", "2025-12-31")
            assert len(filtered) == 2  # 20 déc + 22 déc

    def test_get_date_range(self, tmp_db: Path, sample_items: list[NewsItem]):
        """min/max dates retournées correctement."""
        with NewsDatabase(tmp_db) as db:
            db.upsert_items(sample_items)
            min_d, max_d = db.get_date_range()
            assert min_d == "2025-12-20"
            assert max_d == "2026-01-03"

    def test_empty_db(self, tmp_db: Path):
        """Une BDD vide retourne 0 et None pour les dates."""
        with NewsDatabase(tmp_db) as db:
            assert db.count() == 0
            assert db.get_date_range() == (None, None)
            assert db.get_all_items() == []

    def test_ingest_tags_source(self, tmp_db: Path, sample_items: list[NewsItem]):
        """ingest() tague chaque item avec l'identifiant de source."""
        with NewsDatabase(tmp_db) as db:
            db.ingest(sample_items, source="rss:techcrunch")
            items = db.get_all_items()
            assert all(item.source == "rss:techcrunch" for item in items)

    def test_ingest_different_sources(self, tmp_db: Path):
        """Des items de sources différentes coexistent en BDD."""
        items_a = [NewsItem(category="Tech", sub_category="X", title="A", description="D", date="2025-01-01")]
        items_b = [NewsItem(category="Tech", sub_category="X", title="B", description="D", date="2025-01-02")]
        with NewsDatabase(tmp_db) as db:
            db.ingest(items_a, source="rss:feed1")
            db.ingest(items_b, source="agent:web")
            all_items = db.get_all_items()
            sources = {item.source for item in all_items}
            assert sources == {"rss:feed1", "agent:web"}

    def test_migration_adds_source_column(self, tmp_db: Path, sample_items: list[NewsItem]):
        """La migration ajoute la colonne source sans casser les données existantes."""
        # Simuler une BDD pré-migration (sans colonne source)
        import sqlite3
        conn = sqlite3.connect(str(tmp_db))
        conn.execute("""CREATE TABLE news (
            uid TEXT PRIMARY KEY, category TEXT, sub_category TEXT,
            title TEXT, description TEXT, links TEXT DEFAULT '',
            date TEXT, is_enhanced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )""")
        conn.execute("INSERT INTO news (uid, category, sub_category, title, description, date) VALUES ('old1', 'Tech', 'X', 'Old', 'Desc', '2025-01-01')")
        conn.commit()
        conn.close()

        # Ouvrir avec NewsDatabase → la migration doit ajouter source
        with NewsDatabase(tmp_db) as db:
            items = db.get_all_items()
            assert len(items) == 1
            assert items[0].source == "manual"  # Valeur par défaut
