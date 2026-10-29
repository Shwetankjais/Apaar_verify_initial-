import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import engine, Base
import backend.app.models # Register all models

# API Routers
from backend.app.api.institutions import router as institutions_router
from backend.app.api.uploads import router as uploads_router
from backend.app.api.students import router as students_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.exceptions import router as exceptions_router
from backend.app.api.verification import router as verification_router
from backend.app.api.academic_journey import router as journey_router
from backend.app.api.audit import router as audit_router
from backend.app.api.edupath import router as edupath_router
from backend.app.api.policy_rag import router as policy_router

# Initialize database schema automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="APAAR Verify by Sutrāyukti",
    description="Student Data Management and Academic Record Verification Platform for AICTE-Approved Institutions (SIH 2026 Problem Statement 26263)",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "APAAR Verify Core API",
        "version": settings.VERSION,
        "database": "connected",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "synthetic_demo_mode": True
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to APAAR Verify by Sutrāyukti (AICTE Engine)",
        "docs": "/docs",
        "health": "/health",
        "tagline": "Trusted academic records. Explainable validation. Secure verification."
    }

# Register API v1 routes
app.include_router(institutions_router, prefix=settings.API_V1_STR)
app.include_router(uploads_router, prefix=settings.API_V1_STR)
app.include_router(students_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(exceptions_router, prefix=settings.API_V1_STR)
app.include_router(verification_router) # contains /api/v1/verification-requests and /api/v1/verify
app.include_router(journey_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(edupath_router, prefix=settings.API_V1_STR)
app.include_router(policy_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

