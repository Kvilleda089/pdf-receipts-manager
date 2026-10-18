from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_endpoint_url: str | None = None
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_region: str = "us-east-1"
    s3_bucket: str = "receipts"
    database_url: str
    allowed_asset_hosts: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


    @property
    def allowed_asset_hosts_set(self) -> set[str]:
        """Convierte 'a.com, b.com' en {'a.com', 'b.com'}."""
        return {
            h.strip().lower()
            for h in self.allowed_asset_hosts.split(",")
            if h.strip()
        }

settings = Settings()