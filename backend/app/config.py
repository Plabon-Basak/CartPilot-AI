
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    paypal_mode: str = "sandbox"
    paypal_client_id: str
    paypal_client_secret: str
    paypal_base_url: str = "https://api-m.sandbox.paypal.com"
    frontend_return_url: str = "http://localhost:5173/?paypal=return"
    frontend_cancel_url: str = "http://localhost:5173/?paypal=cancel"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
