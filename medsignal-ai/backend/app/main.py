from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.drugs import router as drugs_router
from app.api.health import router as health_router

app = FastAPI(title="MedSignal AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(drugs_router)
