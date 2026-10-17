from sqlalchemy import select

from app.database.db import ApiClient

BODY = {
    "externalReference": "RES-2026-0001",
    "html": "<html><body><h1>Recibo {{documentNumber}}</h1></body></html>",
}


def test_sin_clave_da_401(client):
    respuesta = client.post("/documents", json=BODY)
    assert respuesta.status_code == 401


def test_clave_invalida_da_401(client):
    respuesta = client.post("/documents", json=BODY, headers={"X-API-Key": "rk_falsa"})
    assert respuesta.status_code == 401


def test_clave_valida_crea_el_documento(client, res_headers):
    respuesta = client.post("/documents", json=BODY, headers=res_headers)
    assert respuesta.status_code == 201
    assert respuesta.json()["documentNumber"] == "RES-000001"


def test_clave_revocada_da_401(client, session_factory, res_headers):
    with session_factory() as session:
        cliente = session.scalar(
            select(ApiClient).where(ApiClient.project == "reservaciones")
        )
        cliente.status = False
        session.commit()

    respuesta = client.post("/documents", json=BODY, headers=res_headers)
    assert respuesta.status_code == 401


def test_otro_proyecto_no_puede_ver_el_documento(client, res_headers, ped_headers):
    creado = client.post("/documents", json=BODY, headers=res_headers)
    numero = creado.json()["documentNumber"]

    propio = client.get(f"/documents/{numero}", headers=res_headers)
    ajeno = client.get(f"/documents/{numero}", headers=ped_headers)

    assert propio.status_code == 200
    assert ajeno.status_code == 404