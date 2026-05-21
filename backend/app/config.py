from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://safesite:safesite_pass@localhost:5432/safesite_db"

    # YOLO
    yolo_weights_path: str = "backend/weights/best.pt"
    frame_skip: int = 3

    # File storage
    upload_dir: str = "backend/uploads"
    output_dir: str = "backend/outputs"
    violation_frames_dir: str = "backend/violation_frames"
    reports_dir: str = "backend/reports"

    # LLM
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Vector DB
    vector_db_path: str = "chroma_db"
    vector_collection_name: str = "safety_policies"

    # Telegram alerts
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # App
    app_env: str = "development"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # Violation engine
    violation_cooldown_seconds: int = 5

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    def ensure_dirs(self) -> None:
        for path_str in (
            self.upload_dir,
            self.output_dir,
            self.violation_frames_dir,
            self.reports_dir,
        ):
            Path(path_str).mkdir(parents=True, exist_ok=True)


settings = Settings()
