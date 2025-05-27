from fastapi import FastAPI
from app.api import encryption_api

app = FastAPI()

app.include_router(encryption_api.router, prefix="/encryption", tags=["encryption"])

@app.get("/")
async def root():
    return {"message": "Encryption service is running"} 