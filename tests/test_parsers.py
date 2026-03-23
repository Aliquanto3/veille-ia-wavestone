"""Tests pour veille_ia.parsers."""

from pathlib import Path

import pytest

from veille_ia.parsers.txt_parser import NewsParser
from veille_ia.parsers.excel_reader import ExcelReader


class TestNewsParser:
    def test_parse_existing_file(self, txt_input_dir: Path):
        """Parse un fichier .txt réel et vérifie le nombre d'items."""
        tech_file = txt_input_dir / "Tech.txt"
        if not tech_file.exists():
            pytest.skip("Fichier Tech.txt absent")
        parser = NewsParser()
        items = parser.parse_file(tech_file)
        assert len(items) > 0
        assert all(item.category for item in items)
        assert all(item.title for item in items)

    def test_parse_nonexistent_file(self):
        """Un fichier inexistant retourne une liste vide."""
        parser = NewsParser()
        items = parser.parse_file(Path("/tmp/does_not_exist.txt"))
        assert items == []

    def test_parse_all_categories_present(self, txt_input_dir: Path):
        """Les 3 fichiers .txt couvrent les 3 catégories."""
        if not txt_input_dir.exists():
            pytest.skip("Dossier input absent")
        parser = NewsParser()
        all_items = []
        for f in txt_input_dir.glob("*.txt"):
            all_items.extend(parser.parse_file(f))
        cats = {item.category for item in all_items}
        assert "Tech" in cats
        assert "Marché" in cats


class TestExcelReader:
    def test_read_vocabulary(self, excel_template: Path):
        """L'onglet _DATA contient des catégories et sous-catégories."""
        with ExcelReader(excel_template) as reader:
            cats, subs = reader.read_vocabulary()
        assert len(cats) >= 3
        assert len(subs) >= 10

    def test_read_news(self, excel_template: Path):
        """L'onglet NEWS contient des items avec des champs remplis."""
        with ExcelReader(excel_template) as reader:
            items = reader.read_news()
        assert len(items) > 0
        assert all(item.title for item in items)
        assert any(item.date for item in items)

    def test_file_not_found(self):
        """Un fichier inexistant lève FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ExcelReader(Path("/tmp/ghost.xlsx"))
