"""Modèle de données pour une actualité de veille IA."""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NewsItem:
    """Représente une actualité unitaire de veille IA.

    Attributes:
        category: Catégorie principale (ex: "Tech", "Marché", "Gouvernance").
        sub_category: Sous-catégorie (ex: "Modèles", "M&A").
        title: Titre de l'actualité.
        description: Corps de l'actualité (peut contenir du HTML si enrichi).
        links: Liste d'URLs sources.
        uid: Identifiant unique généré automatiquement.
        is_enhanced: True si l'item a été enrichi par le LLM.
        date: Date de l'actualité au format YYYY-MM-DD.
        source: Identifiant de la source d'ingestion (ex: "manual:excel", "rss:techcrunch", "agent:web-scanner").
    """

    category: str
    sub_category: str
    title: str
    description: str
    links: List[str] = field(default_factory=list)
    uid: str = field(init=False)
    is_enhanced: bool = False
    date: Optional[str] = None
    source: str = "manual"

    def __post_init__(self) -> None:
        clean_title = re.sub(r"\W+", "", self.title)
        self.uid = f"{clean_title[:15]}_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
