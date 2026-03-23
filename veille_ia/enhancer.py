"""Couche d'enrichissement IA via LLM (Protocol + implémentation Mistral)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Protocol

from veille_ia.config import CATEGORIES, DEFAULT_MODEL, SUB_CATEGORIES
from veille_ia.models import NewsItem

logger = logging.getLogger(__name__)


# --- P8 : Abstraction LLM ---

class LLMClient(Protocol):
    """Interface pour un client LLM (chat completion)."""

    def chat_complete(
        self, model: str, messages: List[Dict[str, str]], **kwargs: Any
    ) -> str:
        """Envoie un message et retourne le contenu texte de la réponse."""
        ...


class MistralLLMClient:
    """Implémentation concrète du LLMClient pour l'API Mistral."""

    def __init__(self, api_key: str):
        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise ImportError("Le module 'mistralai' est requis.") from exc
        self._client = Mistral(api_key=api_key)

    def chat_complete(
        self, model: str, messages: List[Dict[str, str]], **kwargs: Any
    ) -> str:
        response = self._client.chat.complete(model=model, messages=messages, **kwargs)
        return response.choices[0].message.content


# --- P4 : Séparation Enhancer / TeamsReportGenerator ---

class NewsEnhancer:
    """Enrichit les news via LLM (classification, édition, emojis)."""

    def __init__(
        self,
        client: LLMClient,
        model: str = DEFAULT_MODEL,
        batch_size: int = 10,
        categories: List[str] | None = None,
        sub_categories: List[str] | None = None,
    ):
        self.client = client
        self.model = model
        self.batch_size = batch_size
        self.categories = categories or CATEGORIES[:]
        self.sub_categories = sub_categories or SUB_CATEGORIES[:]

    def enhance_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """Enrichit une liste de news par lots."""
        logger.info("🧠 Enrichissement via Mistral (Batch : %d items/appel)...", self.batch_size)
        enhanced: List[NewsItem] = []

        for i in range(0, len(items), self.batch_size):
            chunk = items[i: i + self.batch_size]
            logger.info("   📦 Lot %d...", i // self.batch_size + 1)
            try:
                enhanced.extend(self._process_batch(chunk))
            except Exception as e:
                logger.warning("   ⚠️ Erreur sur le lot: %s. Fallback.", e)
                enhanced.extend(chunk)
            time.sleep(1)

        return enhanced

    def _process_batch(self, batch: List[NewsItem]) -> List[NewsItem]:
        input_data = [
            {"id": item.uid, "category": item.category,
             "sub_category": item.sub_category, "title": item.title,
             "description": item.description}
            for item in batch
        ]

        prompt = f"""
        Tu es un expert en veille technologique et éditeur en chef chez Wavestone.
        Tu vas recevoir une liste d'actualités brutes au format JSON.
        
        Listes de référence (Vocabulaire Contrôlé) :
        - CATEGORIES : {json.dumps(self.categories, ensure_ascii=False)}
        - SOUS-CATEGORIES : {json.dumps(self.sub_categories, ensure_ascii=False)}

        Ta mission pour CHAQUE actualité :
        
        1. **CLASSIFICATION (RÈGLE DE PRÉSERVATION)** :
           - Vérifie les champs 'category' et 'sub_category' reçus en input.
           - **SI** la valeur reçue existe DÉJÀ dans les listes de référence ci-dessus : **TU NE DOIS PAS LA CHANGER**.
           - **SINON** (vide ou inconnue) : Déduis la bonne valeur depuis les listes.
        
        2. **ÉDITION** :
           - Corrige l'orthographe et le style du titre et de la description.
           - Ajoute 1 emoji pertinent au tout début du titre.
           - NE METS PAS de gras dans le TITRE.
           - Utilise <b>, <i> pour les mots-clés dans la DESCRIPTION uniquement.

        Format JSON strict :
        {{
            "items": [
                {{
                    "id": "ID_ORIGINAL",
                    "category": "...",
                    "sub_category": "...",
                    "title": "Emoji + Titre",
                    "description": "Description améliorée..."
                }}
            ]
        }}

        Données Input :
        {json.dumps(input_data, ensure_ascii=False)}
        """

        content = self.client.chat_complete(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        try:
            json_response = json.loads(content)
            output_map = {item["id"]: item for item in json_response.get("items", [])}

            for original in batch:
                data = output_map.get(original.uid)
                if data:
                    original.title = data.get("title", original.title)
                    original.description = data.get("description", original.description)
                    original.category = data.get("category", original.category)
                    original.sub_category = data.get("sub_category", original.sub_category)
                    original.is_enhanced = True
            return batch
        except Exception as e:
            logger.error("      -> Erreur parsing JSON: %s", e)
            return batch


class TeamsReportGenerator:
    """Génère le message d'annonce Teams via LLM."""

    def __init__(self, client: LLMClient, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model

    def generate(self, items: List[NewsItem], date_range: str) -> str:
        """Génère une synthèse pour Microsoft Teams."""
        logger.info("📢 Génération du message Teams...")

        summary_data = [
            {"cat": item.category, "sub": item.sub_category, "title": item.title}
            for item in items
        ]

        prompt = f"""
        Tu es Senior AI Consultant chez Wavestone.
        Rédige un message d'annonce percutant pour le canal Microsoft Teams de la practice IA.
        
        Données (Période : {date_range}) :
        {json.dumps(summary_data, ensure_ascii=False)}

        Consignes :
        1. Ton professionnel, expert, engageant.
        2. Accroche courte avec emojis.
        3. "À la une" : 3 actualités les plus stratégiques, 1 phrase chacune.
        4. Appel à action : Dashboard → https://aliquanto3.github.io/veille-ia-wavestone/
        5. Markdown Teams (gras pour entreprises/technos).
        
        Texte uniquement, sans fioritures.
        """

        try:
            return self.client.chat_complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            ).strip()
        except Exception as e:
            logger.warning("⚠️ Erreur génération Teams : %s", e)
            return "La veille IA de la semaine est disponible sur le portail ! 🚀"
