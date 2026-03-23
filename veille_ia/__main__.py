"""Point d'entrée CLI : python -m veille_ia."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from veille_ia.config import BASE_INPUT_DIR, DB_DEFAULT_PATH
from veille_ia.database import NewsDatabase
from veille_ia.enhancer import MistralLLMClient, NewsEnhancer, TeamsReportGenerator
from veille_ia.renderer import HTMLRenderer
from veille_ia.sources import DbSource, ExcelSource, NewsSource, TxtSource
from veille_ia.utils import format_date_range

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_source(args: argparse.Namespace) -> NewsSource:
    """Factory : construit la source de données selon les arguments CLI."""
    if args.from_db:
        return DbSource(Path(args.db_path), args.date_start, args.date_end)
    if args.excel:
        return ExcelSource(Path(args.excel), args.date_start, args.date_end)
    return TxtSource(args.input_dir, args.date_start, args.date_end)


def setup_output_dirs() -> tuple[Path, Path, Path]:
    """Crée l'arborescence outputs/ et retourne (pages, json, teams)."""
    base = Path("outputs")
    dirs = (base / "pages", base / "TexteMistral", base / "Teams")
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def save_teams_message(message: str, dir_teams: Path, start: str, end: str) -> None:
    """Sauvegarde le message Teams dans outputs/Teams et à la racine."""
    teams_path = dir_teams / f"Annonce_Teams_du_{start}_au_{end}.md"
    teams_path.write_text(message, encoding="utf-8")
    Path("teams_announcement.md").write_text(message, encoding="utf-8")
    logger.info("✅ Message Teams → %s", teams_path)


def save_html_output(content: str, dir_pages: Path, output_arg: str | None) -> None:
    """Sauvegarde le dashboard HTML."""
    if output_arg:
        filename = output_arg if output_arg.endswith(".html") else f"{output_arg}.html"
    else:
        filename = f"Veille_IA_{datetime.now().strftime('%Y-%m-%d')}.html"
    path = dir_pages / filename
    path.write_text(content, encoding="utf-8")
    logger.info("🚀 Dashboard généré : %s", path)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Générateur de Veille IA Wavestone")
    parser.add_argument("--no-mistral", action="store_true", help="Désactiver l'IA")
    parser.add_argument("--save-json", action="store_true", help="Debug JSON")
    parser.add_argument("-o", "--output", type=str, default=None, help="Fichier HTML sortie")
    parser.add_argument("--title", type=str, default="🤖 Veille IA Wavestone", help="Titre")
    parser.add_argument("--subtitle", type=str, default=None, help="Sous-titre")
    parser.add_argument("--date-start", type=str, default="?", help="Format YYYY-MM-DD")
    parser.add_argument("--date-end", type=str, default="?", help="Format YYYY-MM-DD")
    parser.add_argument("--input-dir", type=str, default=BASE_INPUT_DIR, help="Dossier racine")
    parser.add_argument("--excel", type=str, default=None, help="Fichier Excel source")
    parser.add_argument("--db", action="store_true", help="Stocker en BDD après ingestion")
    parser.add_argument("--db-path", type=str, default=str(DB_DEFAULT_PATH), help="Chemin BDD SQLite")
    parser.add_argument("--from-db", action="store_true", help="Générer depuis la BDD")
    args = parser.parse_args()

    # --- Setup ---
    dir_pages, dir_json, dir_teams = setup_output_dirs()

    # --- 1. Chargement des données (Strategy pattern) ---
    source = build_source(args)
    all_items, final_start, final_end = source.load()
    logger.info("📅 Période : %s au %s", final_start, final_end)

    display_range, file_start, file_end = format_date_range(final_start, final_end)

    if not all_items:
        logger.warning("Aucun article trouvé.")
        return

    # --- 2. Enrichissement LLM ---
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not args.no_mistral and not api_key:
        logger.warning("⚠️ Pas de clé API. Mode --no-mistral forcé.")
        args.no_mistral = True

    if not args.no_mistral:
        try:
            assert api_key is not None  # Garanti par le check ci-dessus
            client = MistralLLMClient(api_key=api_key)
            enhancer = NewsEnhancer(client=client)
            all_items = enhancer.enhance_items(all_items)

            reporter = TeamsReportGenerator(client=client)
            teams_message = reporter.generate(all_items, display_range)
            save_teams_message(teams_message, dir_teams, file_start, file_end)
        except ImportError as e:
            logger.warning("⚠️ SDK Mistral non disponible (%s). Enrichissement sauté.", e)
    else:
        logger.info("⏩ Mode No-Mistral : saut de l'enrichissement.")

    # --- 3. Stockage BDD (incrémental) ---
    if args.db and not args.from_db:
        source_tag = "manual:excel" if args.excel else "manual:txt"
        with NewsDatabase(Path(args.db_path)) as db:
            db.ingest(all_items, source=source_tag)
            logger.info("🗄️ BDD : %d news en base.", db.count())

    # --- 4. Export JSON (debug) ---
    if args.save_json:
        json_path = dir_json / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_path.write_text(
            json.dumps([item.to_dict() for item in all_items], indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("💾 JSON → %s", json_path)

    # --- 5. Rendu HTML ---
    subtitle = args.subtitle or f"Généré le {datetime.now().strftime('%d/%m/%Y')} • {len(all_items)} actualités"
    renderer = HTMLRenderer(title=args.title, subtitle=subtitle, date_range=display_range)
    save_html_output(renderer.render(all_items), dir_pages, args.output)


if __name__ == "__main__":
    main()
