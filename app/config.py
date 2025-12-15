import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

# Load variables from a local .env file (if present) before reading os.environ.
load_dotenv()


class Settings(BaseModel):
    """Runtime configuration loaded from environment variables."""

    app_name: str = Field(default="Realtime AI Backend")
    env: str = Field(default=os.getenv("APP_ENV", "local"))
    groq_api_key: str = Field(default=os.getenv("GROQ_API_KEY", ""))
    # Default to a currently supported Groq model; override via GROQ_MODEL env var if needed.
    groq_model: str = Field(default=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))
    supabase_url: str = Field(default=os.getenv("SUPABASE_URL", ""))
    supabase_key: str = Field(default=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))
    supabase_schema: str = Field(default=os.getenv("SUPABASE_SCHEMA", "public"))
    session_summary_max_tokens: int = Field(default=256)
    system_prompt: str = Field(
        default=(
            "You are Zephyr, a realtime AI guide helping sustainability founders "
            "brainstorm features. Keep answers concise, cite any internal tools used, "
            "and ask clarifying questions when the user's intent is unclear."
        )
    )

    @validator("groq_api_key", "supabase_url", "supabase_key", pre=True)
    def strip_strings(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings to avoid re-parsing environment variables."""

    return Settings()

