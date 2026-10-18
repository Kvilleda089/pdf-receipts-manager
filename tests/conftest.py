import os

os.environ["DATABASE_URL"] = "sqlite://"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db import ApiClient, Base, get_session
from app.main import app
from app.security import hash_key

RES_KEY = "rk_test_reservaciones"
PED_KEY = "rk_test_pedidos"

os.environ["DATABASE_URL"] = "sqlite://"


@pytest.fixture
def session_factory():
    """Base de datos temporal en memoria, con dos clientes ya creados."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add(ApiClient(project="reservaciones", key_hash=hash_key(RES_KEY)))
        session.add(ApiClient(project="pedidos", key_hash=hash_key(PED_KEY)))
        session.commit()
    return factory


@pytest.fixture
def client(session_factory, monkeypatch):
    """Cliente de pruebas: base temporal y sin PDF ni S3 reales."""

    def override_get_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr("app.main.render_pdf", lambda html, number: b"%PDF-fake")
    monkeypatch.setattr("app.main.upload_pdf", lambda key, data: f"http://fake-s3/{key}")
    monkeypatch.setattr("app.main.get_url", lambda key: f"http://fake-s3/{key}?nuevo")

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def res_headers():
    return {"X-API-Key": RES_KEY}


@pytest.fixture
def ped_headers():
    return {"X-API-Key": PED_KEY}