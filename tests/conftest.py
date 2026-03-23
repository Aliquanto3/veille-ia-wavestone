"""Fixtures partagées pour les tests."""

from __future__ import annotations

import pytest
from pathlib import Path
from veille_ia.models import NewsItem


@pytest.fixture
def sample_items() -> list[NewsItem]:
    """Retourne une liste de 3 NewsItem de test."""
    return [
        NewsItem(
            category="Tech", sub_category="Modèles",
            title="Test Model Alpha", description="Description du modèle Alpha.",
            links=["https://example.com/alpha"], date="2025-12-20",
        ),
        NewsItem(
            category="Marché", sub_category="M&A",
            title="Acquisition BigCorp", description="BigCorp rachète SmallCo.",
            links=["https://example.com/bigcorp", "https://example.com/smallco"], date="2025-12-22",
        ),
        NewsItem(
            category="Gouvernance", sub_category="RSE",
            title="Bilan carbone IA", description="Rapport sur l'empreinte.",
            links=[], date="2026-01-03",
        ),
    ]


@pytest.fixture
def txt_input_dir() -> Path:
    """Chemin vers les fichiers .txt de test existants."""
    return Path("inputs/2025-12-19_2026-01-05")


@pytest.fixture
def excel_template() -> Path:
    """Chemin vers le template Excel."""
    candidates = [
        Path("inputs/Veille_IA_Template.xlsx"),
        Path("inputs/Veille_IA_Template - 2026-03.xlsx"),
    ]
    for p in candidates:
        if p.exists():
            return p
    pytest.skip("Aucun fichier Excel template trouvé dans inputs/")
