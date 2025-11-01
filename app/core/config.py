from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "autoteile_db"

    # --- JWT ---
    JWT_SECRET: str = "super_secret_key"  # лучше задать в .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str | None = None  # можно задать в .env

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Настройки Pydantic v2
    model_config = ConfigDict(env_file=".env")


settings = Settings()
