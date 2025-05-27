from fastapi import FastAPI
from app.api import encryption_api
from app.core.config import settings

app = FastAPI(
    title="Encryption Service with Celery and WebSockets",
    description="Lab 3: Asynchronous API for data encryption/decryption",
    version="0.3.0"
)

app.include_router(encryption_api.router, prefix="/encryption", tags=["Encryption REST & WebSocket"])

@app.on_event("startup")
async def startup_event():
    print("Application startup...")
    print(f"Celery Broker: {settings.CELERY_BROKER_URL}")
    print(f"Celery Backend: {settings.CELERY_RESULT_BACKEND}")
    print("WebSocket endpoint available at /encryption/ws/{client_id}")
    print("REST endpoints available at /encryption/encode/{client_id} and /encryption/decode/{client_id}")

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown...")

@app.get("/")
async def root():
    return {"message": "Welcome to the Encryption Service! See /docs for API details."}

