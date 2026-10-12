from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    """Acepta nombres en camelCase (taxId) y en snake_case (tax_id)."""

    model_config = ConfigDict(populate_by_name=True)


class Party(CamelModel):
    name: str
    tax_id: str | None = Field(default=None, alias="taxId")
    email: str | None = None
    address: str | None = None


class Issuer(Party):
    logo_url: str | None = Field(default=None, alias="logoUrl")


class Item(CamelModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(alias="unitPrice", ge=0)

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.unit_price


class Payment(CamelModel):
    label: str
    amount: Decimal = Field(ge=0)


class ReceiptRequest(CamelModel):
    project: str
    template: str = "default"
    external_reference: str = Field(alias="externalReference")
    issue_date: date | None = Field(default=None, alias="issueDate")
    currency: str = "GTQ"
    issuer: Issuer
    customer: Party
    items: list[Item] = Field(min_length=1)
    payments: list[Payment] = []
    notes: str | None = None
    metadata: dict = {}

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    @property
    def paid(self) -> Decimal:
        return sum((p.amount for p in self.payments), Decimal("0"))

    @property
    def balance(self) -> Decimal:
        return self.total - self.paid


class ReceiptResponse(CamelModel):
    receipt_number: str = Field(alias="receiptNumber")
    pdf_url: str = Field(alias="pdfUrl")
    total: Decimal
    paid: Decimal
    balance: Decimal