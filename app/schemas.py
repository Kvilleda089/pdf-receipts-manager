from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    """Acepta nombres en camelCase (externalReference) y en snake_case."""
    model_config = ConfigDict(populate_by_name=True)


class DocumentRequest(CamelModel):
    external_reference: str = Field(
        alias="externalReference", min_length=1, max_length=100
    )
    html: str = Field(min_length=1, max_length=2_000_000)
    metadata: dict = {}


class DocumentResponse(CamelModel):
    document_number: str = Field(alias="documentNumber")
    external_reference: str = Field(alias="externalReference")
    pdf_url: str = Field(alias="pdfUrl")