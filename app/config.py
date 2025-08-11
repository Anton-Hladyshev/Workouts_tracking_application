from pydantic_settings import BaseSettings
from dotenv import dotenv_values

config = dotenv_values(".env")

class Settings(BaseSettings):
    DB_HOST: str | None = config.get("HOST", "loacalhost")
    DB_PORT: str | None = config.get("POSTGRES_PORT", "5432")
    DB_USER: str | None = config.get("POSTGRES_USER")
    DB_PASSWORD: str | None = config.get("POSTGRES_PASSWORD")
    DB_NAME: str | None = config.get("POSTGRES_DB")

    # DSN: postgresql+psycopg://admin:admin@localhost:5432/club_db
    @property # called as settings.db_url
    def get_db_url_with_psycopg(self) -> str:
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # DSN: postgresql+asyncpg://admin:admin@localhost:5432/club_db
    @property
    def get_db_url_with_asyncpg(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
settings = Settings()