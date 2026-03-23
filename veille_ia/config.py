"""Configuration centralisée du pipeline de veille IA."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

# --- Vocabulaire contrôlé (valeurs par défaut) ---
CATEGORIES: List[str] = ["Marché", "Tech", "Gouvernance"]
SUB_CATEGORIES: List[str] = [
    "Souveraineté", "M&A", "Conseil", "Stratégie", "Economie",
    "Modèles", "Providers", "Développement", "Robotique",
    "Evaluation", "RSE", "Cybersécurité", "Conformité", "RH",
]

# --- LLM ---
DEFAULT_MODEL: str = os.environ.get("MISTRAL_MODEL", "mistral-small-2603")

# --- Paths ---
DB_DEFAULT_PATH: Path = Path("data/veille_ia.db")
BASE_OUTPUT_DIR: Path = Path("outputs")
BASE_INPUT_DIR: str = "inputs"

# --- Assets ---
ASSETS_DIR: Path = Path(__file__).parent / "assets"
