from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./db_absensi.db"
    secret_key: str = "ganti-di-production"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 8
    frontend_origins: str = "http://127.0.0.1:8000,http://localhost:8000"
    qr_expire_minutes: int = 15

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
