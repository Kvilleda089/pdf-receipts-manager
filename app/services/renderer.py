from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from weasyprint import HTML


from app.schemas import ReceiptRequest

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

SYMBOLS = {"GTQ": "Q", "USD": "$"}

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)

def money(value) -> str:
    """600 -> 600.00 ; 1234.5 -> 1,234.50"""
    return f"{value:,.2f}"

env.filters["money"] = money

def render_receipt_pdf(receipt: ReceiptRequest, receipt_number: str) -> bytes:
    """Convierte un recibo en un PDF (bytes)."""
    try:
        template = env.get_template(f"{receipt.template}.html")
    except TemplateNotFound:
        template = env.get_template("default.html")

    html = template.render(
        receipt=receipt,
        number=receipt_number,
        issue_date=receipt.issue_date or date.today(),
        symbol=SYMBOLS.get(receipt.currency, receipt.currency),
        total= receipt.total,
        paid=receipt.paid,
        balance=receipt.balance,
    )
    return HTML(string=html).write_pdf()
