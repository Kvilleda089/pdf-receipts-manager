import logging


from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.db import (
    DocumentRecord,
    get_session,
    init_db,
    next_document_number,
)
from app.schemas import DocumentRequest, DocumentResponse
from app.services.renderer import render_pdf
from app.services.storage import ensure_bucket, get_url, upload_pdf
from app.security import get_api_project

logging.basicConfig(level=logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_bucket()
    yield


app = FastAPI(title="PDF Receipts Manager", lifespan=lifespan)

MAX_BODY_BYTES = 3_000_000  # 3 MB


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length:
        try:
            too_big = int(length) > MAX_BODY_BYTES
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Cabecera inválida"})
        if too_big:
            return JSONResponse(
                status_code=413, content={"detail": "Petición demasiado grande"}
            )
    return await call_next(request)

@app.get("/health")
def health():
    return {"status": "ok", "bucket": settings.s3_bucket}


@app.post("/documents", response_model=DocumentResponse, status_code=201)
def create_document(
    request: DocumentRequest,
    session: Session = Depends(get_session),
    project: str = Depends(get_api_project),
):
    number = next_document_number(session, project)
    pdf = render_pdf(request.html, number)

    key = f"{project}/{date.today().year}/{number}.pdf"
    pdf_url = upload_pdf(key, pdf)

    session.add(
        DocumentRecord(
            document_number=number,
            project=project,
            external_reference=request.external_reference,
            pdf_key=key,
            meta=request.metadata,
        )
    )
    session.commit()

    return DocumentResponse(
        document_number=number,
        external_reference=request.external_reference,
        pdf_url=pdf_url,
    )


@app.get("/documents/{document_number}", response_model=DocumentResponse)
def get_document(
    document_number: str,
    session: Session = Depends(get_session),
    project: str = Depends(get_api_project),
):
    record = session.scalar(
        select(DocumentRecord).where(DocumentRecord.document_number == document_number)
    )
    if record is None or record.project != project:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return DocumentResponse(
        document_number=record.document_number,
        external_reference=record.external_reference,
        pdf_url=get_url(record.pdf_key),
    )