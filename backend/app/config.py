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
    
    # Environment mode
    ENVIRONMENT: str = os.getenv("APP_ENV", "development")

settings = Settings()

