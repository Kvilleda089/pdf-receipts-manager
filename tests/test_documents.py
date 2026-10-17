from datetime import date

import pytest

BODY = {
    "externalReference": "RES-2026-0001",
    "html": "<html><body><h1>Recibo {{documentNumber}}</h1></body></html>",
}


def test_numeracion_correlativa_por_proyecto(client, res_headers, ped_headers):
    r1 = client.post("/documents", json=BODY, headers=res_headers)
    r2 = client.post("/documents", json=BODY, headers=res_headers)
    p1 = client.post("/documents", json=BODY, headers=ped_headers)

    assert r1.json()["documentNumber"] == "RES-000001"
    assert r2.json()["documentNumber"] == "RES-000002"
    assert p1.json()["documentNumber"] == "PED-000001"


def test_la_respuesta_trae_referencia_y_enlace(client, res_headers):
    respuesta = client.post("/documents", json=BODY, headers=res_headers)
    datos = respuesta.json()

    assert datos["externalReference"] == "RES-2026-0001"
    assert datos["pdfUrl"] == (
        f"http://fake-s3/reservaciones/{date.today().year}/RES-000001.pdf"
    )


def test_consultar_devuelve_un_enlace_nuevo(client, res_headers):
    creado = client.post("/documents", json=BODY, headers=res_headers).json()

    consulta = client.get(
        f"/documents/{creado['documentNumber']}", headers=res_headers
    )

    assert consulta.status_code == 200
    assert consulta.json()["pdfUrl"].endswith("?nuevo")


def test_consultar_un_documento_que_no_existe_da_404(client, res_headers):
    respuesta = client.get("/documents/RES-999999", headers=res_headers)
    assert respuesta.status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {"externalReference": "RES-1", "html": ""},
        {"html": "<p>hola</p>"},
        {"externalReference": "RES-1"},
    ],
)
def test_peticion_incompleta_da_422(client, res_headers, body):
    respuesta = client.post("/documents", json=body, headers=res_headers)
    assert respuesta.status_code == 422


def test_peticion_demasiado_grande_da_413(client):
    body = {"externalReference": "RES-1", "html": "x" * 4_000_000}
    respuesta = client.post("/documents", json=body)

    assert respuesta.status_code == 413
    assert respuesta.json()["detail"] == "Petición demasiado grande"


def test_el_proyecto_sale_de_la_clave_y_no_del_body(client, res_headers):
    body = {**BODY, "project": "pedidos"}
    respuesta = client.post("/documents", json=body, headers=res_headers)

    assert respuesta.status_code == 201
    assert respuesta.json()["documentNumber"].startswith("RES-")