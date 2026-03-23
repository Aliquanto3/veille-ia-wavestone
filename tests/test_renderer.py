"""Tests pour veille_ia.renderer."""

from veille_ia.models import NewsItem
from veille_ia.renderer import HTMLRenderer, sanitize_html


class TestSanitizeHtml:
    def test_escape_script(self):
        assert "&lt;script&gt;" in sanitize_html("<script>alert(1)</script>")

    def test_preserve_allowed_tags(self):
        result = sanitize_html("<b>bold</b> and <i>italic</i>", allow_tags=True)
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result

    def test_escape_non_allowed_with_allowed_on(self):
        result = sanitize_html("<b>ok</b><script>bad</script>", allow_tags=True)
        assert "<b>ok</b>" in result
        assert "&lt;script&gt;" in result

    def test_plain_text_passthrough(self):
        assert sanitize_html("Hello world") == "Hello world"


class TestHTMLRenderer:
    def test_render_returns_html(self, sample_items: list[NewsItem]):
        renderer = HTMLRenderer(title="Test", subtitle="Sub", date_range="Test range")
        html = renderer.render(sample_items)
        assert "<!DOCTYPE html>" in html
        assert "Test" in html
        assert "data-cat=" in html

    def test_render_includes_date_filter(self, sample_items: list[NewsItem]):
        renderer = HTMLRenderer(title="T", subtitle="S", date_range="R")
        html = renderer.render(sample_items)
        assert 'id="dateStart"' in html
        assert 'id="dateEnd"' in html

    def test_render_includes_date_badges(self, sample_items: list[NewsItem]):
        renderer = HTMLRenderer(title="T", subtitle="S", date_range="R")
        html = renderer.render(sample_items)
        assert "news-date-badge" in html
        assert "2025-12-20" in html

    def test_render_empty_list(self):
        renderer = HTMLRenderer(title="T", subtitle="S", date_range="R")
        html = renderer.render([])
        assert "<!DOCTYPE html>" in html
