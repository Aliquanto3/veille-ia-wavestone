"""Fonctions utilitaires pour le pipeline de veille IA."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def resolve_input_directory(
    base_input_dir: str, arg_start: str, arg_end: str
) -> Tuple[Path, str, str]:
    """
    Détermine le dossier source et les dates.
    Priorité 1 : Dates fournies en argument.
    Priorité 2 : Le dossier le plus récent dans inputs/.
    """
    base_path = Path(base_input_dir)
    if not base_path.exists():
        base_path.mkdir(exist_ok=True)

    if arg_start != "?" and arg_end != "?":
        potential_dir_name = f"{arg_start}_{arg_end}"
        target_path = base_path / potential_dir_name
        if target_path.exists():
            return target_path, arg_start, arg_end
        logger.warning("⚠️ Dossier '%s' introuvable. Recherche automatique...", potential_dir_name)

    dir_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})")
    valid_dirs = []

    for d in base_path.iterdir():
        if d.is_dir():
            match = dir_pattern.match(d.name)
            if match:
                valid_dirs.append((d, match.group(1), match.group(2)))

    if not valid_dirs:
        logger.info("ℹ️ Aucun sous-dossier daté. Utilisation de '%s'.", base_input_dir)
        today = datetime.now()
        curr = today - timedelta(days=today.weekday())
        prev = curr - timedelta(weeks=1)
        return base_path, prev.strftime("%Y-%m-%d"), curr.strftime("%Y-%m-%d")

    valid_dirs.sort(key=lambda x: x[2], reverse=True)
    best_dir, start, end = valid_dirs[0]
    return best_dir, start, end


def format_date_range(start: str, end: str) -> Tuple[str, str, str]:
    """
    Retourne (display_range, file_date_start, file_date_end).
    Gère les erreurs de format gracieusement.
    """
    try:
        d_s = datetime.strptime(start, "%Y-%m-%d")
        d_e = datetime.strptime(end, "%Y-%m-%d")
        display = f"Semaine du {d_s.strftime('%d/%m')} au {d_e.strftime('%d/%m')}"
        return display, d_s.strftime("%d-%m"), d_e.strftime("%d-%m")
    except ValueError:
        display = f"Période : {start} au {end}"
        return display, start.replace("/", "-"), end.replace("/", "-")
