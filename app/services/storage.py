import boto3

from app.config import settings


s3 = boto3.client(
    "s3",
    endpoint_url=settings.aws_endpoint_url,
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)


def ensure_bucket() -> None:
    """Crea el bucket si no existe."""
    try:
        s3.head_bucket(Bucket=settings.s3_bucket)
    except Exception:
        s3.create_bucket(Bucket=settings.s3_bucket)

def upload_file(key: str, data: bytes, content_type: str) -> str:
    """Sube un archivo a S3 y devuelve una URL temporal (1 hora)."""
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return get_url(key)

def get_url(key: str, expires: int=3600) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires,
    )

def upload_pdf(key: str, data: bytes) -> str:
    """Sube un PDF y devuelve una URL temporal (1 hora)."""
    return upload_file(key, data, "application/pdf")