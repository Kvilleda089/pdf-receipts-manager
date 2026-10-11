from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="PDF Receipts Manager")


@app.get("/health")
def health():
    return {"status": "ok", "bucket": settings.s3_bucket}