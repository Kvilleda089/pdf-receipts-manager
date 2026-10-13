import re

from weasyprint import HTML

# Acepta {{documentNumber}} y también {{ documentNumber }}
NUMBER_PLACEHOLDER = re.compile(r"\{\{\s*documentNumber\s*\}\}")


def render_pdf(html: str, document_number: str) -> bytes:
    """Reemplaza el marcador por el número y convierte el HTML a PDF."""
    html = NUMBER_PLACEHOLDER.sub(lambda _: document_number, html)
    return HTML(string=html).write_pdf()