import re
from urllib.parse import urlparse

from weasyprint import HTML
from weasyprint.urls import URLFetcher

from app.config import settings

# Acepta {{documentNumber}} y también {{ documentNumber }}
NUMBER_PLACEHOLDER = re.compile(r"\{\{\s*documentNumber\s*\}\}")


class SafeURLFetcher(URLFetcher):
    """Solo deja pasar recursos incrustados (data:) o de dominios autorizados."""

    def fetch(self, url, headers=None):
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme == "data":
            return super().fetch(url, headers)

        if scheme in ("http", "https"):
            host = (parsed.hostname or "").lower()
            if host in settings.allowed_asset_hosts_set:
                return super().fetch(url, headers)
            raise ValueError(f"Dominio no permitido: {host}")

        raise ValueError(f"Protocolo no permitido: {scheme or 'desconocido'}")


def render_pdf(html: str, document_number: str) -> bytes:
    """Reemplaza el marcador por el número y convierte el HTML a PDF."""
    html = NUMBER_PLACEHOLDER.sub(lambda _: document_number, html)
    fetcher = SafeURLFetcher(
        timeout=10,
        allowed_protocols=["data", "http", "https"],
        allow_redirects=False,
    )
    return HTML(string=html, url_fetcher=fetcher).write_pdf()