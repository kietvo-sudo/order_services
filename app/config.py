from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "order-service"
    app_env: str = "development"
    app_port: int = 8000

    db_host: str = "localhost"
    db_port: int = 5434
    db_user: str = "order_user"
    db_password: str = "order123"
    db_name: str = "order_db"
    database_url: str | None = None  # Optional full URL override

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()

