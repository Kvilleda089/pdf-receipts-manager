import hashlib

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import ApiClient, get_session


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def hash_key(key: str) -> str:
    """Clave para el proyecto. En la base solo se guarda esto"""
    return hashlib.sha256(key.encode()).hexdigest()

def get_api_project(
    api_key: str | None = Security(api_key_header),
    session: Session = Depends(get_session),
) -> str:
    """Devuelve el proyecto dueño de la clave o responde 401"""
    if api_key:
        client = session.scalar(
            select(ApiClient).where(
                ApiClient.key_hash == hash_key(api_key),
                ApiClient.status.is_(True),
            )
        )
        if client is not None:
            return client.project

    raise HTTPException(status_code=401, detail="API Key inválida o ausente")