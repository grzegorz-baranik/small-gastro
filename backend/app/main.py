from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1.router import api_router
from app.core.middleware import LanguageMiddleware

settings = get_settings()

app = FastAPI(
    title="Small Gastro API",
    description="API dla aplikacji do zarzadzania mala gastronomia",
    version="1.0.0",
)

# Add language detection middleware (must be added before CORS)
app.add_middleware(LanguageMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
