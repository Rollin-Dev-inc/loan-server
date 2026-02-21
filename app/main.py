from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import CORS_ORIGINS
from app.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Rental Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def add_watermark_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "Rollindev | Pabloraka"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
