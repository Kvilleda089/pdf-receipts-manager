from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_endpoint_url: str | None = None
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_region: str = "us-east-1"
    s3_bucket: str = "receipts"
    database_url: str = "sqlite:///./receipts.db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()