from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

from app.config import settings

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Counter(Base):
    """Último número usado por cada proyecto."""

    __tablename__= "counters"

    project: Mapped[str] = mapped_column(String(50), primary_key=True)
    last_number: Mapped[int] = mapped_column(Integer, default=0)

class ReceiptRecord(Base):
     """Un recibo emitido."""

     __tablename__ = "receipts"

     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
     receipt_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
     project: Mapped[str] = mapped_column(String(50), index=True)
     external_reference: Mapped[str] = mapped_column(String(100), index=True)
     customer_name: Mapped[str] = mapped_column(String(200))
     currency: Mapped[str] = mapped_column(String(3))
     total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
     paid: Mapped[Decimal] = mapped_column(Numeric(12, 2))
     balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
     pdf_key: Mapped[str] = mapped_column(String(300))
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

def next_receipt_number(session: Session, project: str) -> str:
    """RES-000001, RES-000002... un contador independiente por proyecto."""
    counter = session.get(Counter, project)
    if counter is None:
        counter = Counter(project=project, last_number=0)
        session.add(counter)
    counter.last_number +=1
    session.flush()
    return f"{project[:3].upper()}-{counter.last_number:06d}"