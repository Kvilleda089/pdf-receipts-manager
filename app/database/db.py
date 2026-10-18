from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.exc import IntegrityError

from app.config import settings

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(
    settings.database_url, 
    connect_args=connect_args,
    pool_pre_ping=True,
    )
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Counter(Base):
    """Último número usado por cada proyecto."""

    __tablename__ = "counters"

    project: Mapped[str] = mapped_column(String(50), primary_key=True)
    last_number: Mapped[int] = mapped_column(Integer, default=0)


class ApiClient(Base):
    """Una API Key de una aplicación. Un proyecto puede tener varias."""

    __tablename__ = "api_clients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project: Mapped[str] = mapped_column(String(100), index=True)
    key_hash: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)

    )
    

class DocumentRecord(Base):
    """Un documento PDF generado."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    project: Mapped[str] = mapped_column(String(50), index=True)
    external_reference: Mapped[str] = mapped_column(String(100), index=True)
    pdf_key: Mapped[str] = mapped_column(String(300))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def init_db() -> None:
    """Crea las tablas si no existen."""
    Base.metadata.create_all(engine)


def get_session():
    with SessionLocal() as session:
        yield session


def next_document_number(session: Session, project: str) -> str:
    """RES-000001, RES-000002... un contador independiente por proyecto."""
    counter = session.get(Counter, project, with_for_update=True)

    if counter is None:
        try:
            session.add(Counter(project=project, last_number=0))
            session.flush()
        except IntegrityError:
            session.rollback()
        counter = session.get(Counter, project, with_for_update=True)

    counter.last_number += 1
    session.flush()
    return f"{project[:3].upper()}-{counter.last_number:06d}"