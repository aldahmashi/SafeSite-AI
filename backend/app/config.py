from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Root .env lives two levels above this file: backend/app/config.py → project root
_ROOT_ENV = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(_ROOT_ENV), ".env"],  # root first, then local backend/.env overrides
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://safesite:safesite_pass@localhost:5432/safesite_db"

    # YOLO
    yolo_weights_path: str = "weights/best.pt"
    frame_skip: int = 1

    # File storage
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    violation_frames_dir: str = "violation_frames"
    reports_dir: str = "reports"

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

    # Detection
    detection_confidence: float = 0.40  # balanced: fewer false positives
    person_confidence: float = 0.35     # slightly lower for person class
    detection_iou: float = 0.45         # NMS IoU — lower = more aggressive overlap removal
    min_person_area: int = 4000         # ignore tiny far-away persons (px²)

    # Violation engine
    violation_cooldown_seconds: int = 10  # 10 s between same-worker same-violation records

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
