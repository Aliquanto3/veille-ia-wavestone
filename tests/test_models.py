"""Tests pour veille_ia.models."""

from veille_ia.models import NewsItem


def test_newsitem_uid_unique():
    """Deux items avec le même titre ont des UIDs différents."""
    a = NewsItem(category="Tech", sub_category="Modèles", title="Same Title", description="Desc A")
    b = NewsItem(category="Tech", sub_category="Modèles", title="Same Title", description="Desc B")
    assert a.uid != b.uid


def test_newsitem_to_dict():
    """to_dict() retourne un dictionnaire sérialisable."""
    item = NewsItem(category="Tech", sub_category="Modèles", title="Test", description="Desc", date="2025-12-20")
    d = item.to_dict()
    assert d["category"] == "Tech"
    assert d["date"] == "2025-12-20"
    assert isinstance(d["links"], list)


def test_newsitem_default_date_is_none():
    """Par défaut, date est None."""
    item = NewsItem(category="Tech", sub_category="X", title="T", description="D")
    assert item.date is None
