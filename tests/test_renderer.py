import pytest
from weasyprint.urls import URLFetcher

from app.config import settings
from app.services import renderer
from app.services.renderer import SafeURLFetcher, render_pdf


class FakeHTML:
    """Sustituye a WeasyPrint para ver qué HTML recibe."""

    recibido = None

    def __init__(self, string, url_fetcher):
        FakeHTML.recibido = string

    def write_pdf(self):
        return b"%PDF-fake"


def test_el_marcador_se_reemplaza_por_el_numero(monkeypatch):
    monkeypatch.setattr(renderer, "HTML", FakeHTML)

    pdf = render_pdf("<p>{{documentNumber}}</p><p>{{ documentNumber }}</p>", "RES-000007")

    assert pdf == b"%PDF-fake"
    assert FakeHTML.recibido == "<p>RES-000007</p><p>RES-000007</p>"


def test_genera_un_pdf_real():
    pdf = render_pdf("<h1>Hola {{documentNumber}}</h1>", "RES-000001")
    assert pdf.startswith(b"%PDF")


@pytest.fixture
def fetcher():
    return SafeURLFetcher(
        timeout=10,
        allowed_protocols=["data", "http", "https"],
        allow_redirects=False,
    )


@pytest.fixture
def descargas(monkeypatch):
    """Simula la descarga real y anota qué direcciones llegaron a pedirse."""
    pedidas = []

    def falsa(self, url, headers=None):
        pedidas.append(url)
        return "DESCARGADO"

    monkeypatch.setattr(URLFetcher, "fetch", falsa)
    return pedidas


@pytest.fixture(autouse=True)
def sin_dominios_permitidos(monkeypatch):
    """Cada prueba parte con la lista de dominios vacía."""
    monkeypatch.setattr(settings, "allowed_asset_hosts", "")


def test_bloquea_archivos_locales(fetcher, descargas):
    with pytest.raises(ValueError, match="Protocolo no permitido"):
        fetcher.fetch("file:///C:/Windows/win.ini")
    assert descargas == []


def test_bloquea_otros_protocolos(fetcher, descargas):
    with pytest.raises(ValueError, match="Protocolo no permitido"):
        fetcher.fetch("ftp://servidor.com/logo.png")
    assert descargas == []


def test_bloquea_dominios_que_no_estan_en_la_lista(fetcher, descargas):
    with pytest.raises(ValueError, match="Dominio no permitido"):
        fetcher.fetch("https://www.python.org/static/img/python-logo.png")
    assert descargas == []


def test_permite_dominios_de_la_lista(fetcher, descargas, monkeypatch):
    monkeypatch.setattr(settings, "allowed_asset_hosts", "logos.ejemplo.com")

    resultado = fetcher.fetch("https://Logos.Ejemplo.com/logo.png")

    assert resultado == "DESCARGADO"
    assert descargas == ["https://Logos.Ejemplo.com/logo.png"]


def test_no_se_deja_enganar_por_el_truco_de_la_arroba(fetcher, descargas, monkeypatch):
    monkeypatch.setattr(settings, "allowed_asset_hosts", "logos.ejemplo.com")

    with pytest.raises(ValueError, match="Dominio no permitido"):
        fetcher.fetch("http://logos.ejemplo.com@sitio-malo.com/logo.png")
    assert descargas == []


def test_permite_imagenes_incrustadas(fetcher, descargas):
    resultado = fetcher.fetch("data:image/png;base64,AAAA")
    assert resultado == "DESCARGADO"