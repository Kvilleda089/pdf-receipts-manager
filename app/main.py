from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.db import ReceiptRecord, get_session, init_db, next_receipt_number
from app.schemas import ReceiptRequest, ReceiptResponse
from app.services.renderer import render_receipt_pdf
from app.services.storage import ensure_bucket, get_url, upload_pdf


@asynccontextmanager
async def lifespan(app: FastAPI): 
    init_db()
    ensure_bucket()
    yield


app = FastAPI(title="PDF Receipts Manager", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "bucket": settings.s3_bucket}

@app.post("/receipts", response_model=ReceiptResponse, status_code=201)
def create_receipt(
    receipt: ReceiptRequest,
    session: Session = Depends(get_session),
):
    number = next_receipt_number(session, receipt.project)
    pdf = render_receipt_pdf(receipt, number)

    year = (receipt.issue_date or date.today()).year
    key = f"{receipt.project}/{year}/{number}.pdf"
    pdf_url = upload_pdf(key, pdf)

    session.add(
        ReceiptRecord(
            receipt_number=number,
            project=receipt.project,
            external_reference=receipt.external_reference,
            customer_name=receipt.customer.name,
            currency=receipt.currency,
            total=receipt.total,
            paid=receipt.paid,
            balance=receipt.balance,
            pdf_key=key,
        )
    )
    session.commit()

    return ReceiptResponse(
        receipt_number=number,
        pdf_url=pdf_url,
        total=receipt.total,
        paid=receipt.paid,
        balance=receipt.balance,
    )

@app.get("/receipts/{receipt_number}", response_model=ReceiptResponse)
def get_receipt(
    receipt_number: str,
    session: Session = Depends(get_session),
):
    record = session.scalar(
        select(ReceiptRecord).where(ReceiptRecord.receipt_number == receipt_number)
    )

    if record is None:
        raise HTTPException(status_code=404, detail="Recibo no encontrado")

    return ReceiptResponse(
        receipt_number=record.receipt_number,
        pdf_url=get_url(record.pdf_key),
        total=record.total,
        paid=record.paid,
        balance=record.balance,
    )