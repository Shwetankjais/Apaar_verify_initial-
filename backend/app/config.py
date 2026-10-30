import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    PROJECT_NAME: str = "APAAR Verify by Sutrāyukti"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database URL: defaults to local SQLite file for zero-friction runnable demo,
    # or can connect to PostgreSQL if DATABASE_URL is supplied in .env
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR}/apaar_verify.db"
    )
    
    # Cryptographic keys and salts for demo token protection and signatures
    APAAR_SALT: str = os.getenv("APAAR_SALT", "sutrayukti_apaar_salt_sih2026")
    SIGNING_SECRET: str = os.getenv("SIGNING_SECRET", "sutrayukti_tamper_proof_secret_key_2026")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "sutrayukti_tamper_proof_secret_key_2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Private storage directory for student documents
    STORAGE_DIR: Path = BASE_DIR / "storage" / "documents"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024 # 10 MB
    ALLOWED_UPLOAD_EXTENSIONS: set = {".pdf", ".jpeg", ".jpg", ".png"}

    # Environment mode
    ENVIRONMENT: str = os.getenv("APP_ENV", "development")

settings = Settings()

# Ensure storage directory exists
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
