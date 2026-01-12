from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    app_name: str = Field(default="order-service", description="Application name")
    app_env: str = Field(default="development", description="Application environment")
    app_port: int = Field(
        default=8000,
        description="Application port. Can be overridden by PORT environment variable (used by cloud platforms like Render)."
    )
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins. Use '*' for all origins (development only) or list specific origins. https://orders-2ch8.onrender.com is automatically added if not using wildcard."
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    cors_allow_methods: list[str] = Field(
        default=["*"],
        description="Allowed HTTP methods. Use ['*'] for all methods."
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed HTTP headers. Use ['*'] for all headers."
    )

    # Database connection settings
    # Option 1: Use DATABASE_URL (recommended for cloud databases like Neon)
    database_url: str | None = Field(
        default=None,
        description="Full database URL (overrides individual connection parameters if set). "
                   "Use format: postgresql+psycopg2://user:password@host:port/database?sslmode=require"
    )
    
    # Option 2: Use individual parameters (required if DATABASE_URL is not set)
    db_host: str | None = Field(default=None, description="Database host")
    db_port: int | None = Field(default=None, description="Database port")
    db_user: str | None = Field(default=None, description="Database user")
    db_password: str | None = Field(default=None, description="Database password")
    db_name: str | None = Field(default=None, description="Database name")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_database_config(self):
        """Validate that either DATABASE_URL or all individual DB parameters are provided."""
        if self.database_url:
            # If DATABASE_URL is set, ensure it uses psycopg2 driver
            if self.database_url.startswith("postgresql://"):
                self.database_url = self.database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return self
        
        # If DATABASE_URL is not set, all individual parameters are required
        if not all([self.db_host, self.db_port, self.db_user, self.db_password, self.db_name]):
            raise ValueError(
                "Either DATABASE_URL must be set, or all of DB_HOST, DB_PORT, DB_USER, "
                "DB_PASSWORD, and DB_NAME must be provided."
            )
        return self

    @field_validator("db_port")
    @classmethod
    def validate_db_port(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 65535):
            raise ValueError("db_port must be between 1 and 65535")
        return v

    @field_validator("app_port", mode="before")
    @classmethod
    def get_port_from_env(cls, v: int | None) -> int:
        """
        Get port from PORT environment variable (used by cloud platforms like Render).
        Falls back to app_port or default 8000.
        """
        import os
        port_env = os.getenv("PORT")
        if port_env:
            try:
                port = int(port_env)
                if not (1 <= port <= 65535):
                    raise ValueError("PORT must be between 1 and 65535")
                return port
            except ValueError as e:
                # If PORT env var is invalid, fall back to app_port
                pass
        # Use app_port if provided, otherwise default to 8000
        port = v if v is not None else 8000
        if not (1 <= port <= 65535):
            raise ValueError("app_port must be between 1 and 65535")
        return port

    @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def parse_list_from_string(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated string or JSON list from environment variable."""
        if isinstance(v, str):
            # Handle comma-separated string
            if v.strip() == "*":
                return ["*"]
            # Split by comma and strip whitespace
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @model_validator(mode="after")
    def validate_cors_config(self):
        """
        Validate CORS configuration.
        If allow_origins contains ["*"], allow_credentials must be False (CORS spec requirement).
        Also ensures https://orders-2ch8.onrender.com is included if not using wildcard.
        Supports IP address access for development (http://54.254.10.201:8000).
        """
        # Check if wildcard is in the list
        has_wildcard = "*" in self.cors_origins
        
        if has_wildcard and self.cors_allow_credentials:
            # CORS spec violation: cannot use wildcard origin with credentials
            # Auto-fix: set allow_credentials to False
            self.cors_allow_credentials = False
        
        # If not using wildcard, ensure https://orders-2ch8.onrender.com is included
        if not has_wildcard:
            # Add the default Render domain if not already present
            if "https://orders-2ch8.onrender.com" not in self.cors_origins:
                self.cors_origins.append("https://orders-2ch8.onrender.com")
            
            # Add IP address origins for development (if not already present)
            ip_origins = [
                "http://54.254.10.201:8000",
                "http://localhost:8000",
                "http://127.0.0.1:8000"
            ]
            for ip_origin in ip_origins:
                if ip_origin not in self.cors_origins:
                    self.cors_origins.append(ip_origin)
        
        return self

    @property
    def sqlalchemy_url(self) -> str:
        """Generate SQLAlchemy connection URL."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()

