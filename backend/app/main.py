from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# подключаем роуты
from app.api.v1.router import router as api_router
from app.db.models.base import Base
from app.db.db_session import engine

# подключаем модели
from app.db import models
from app.db.seed import seed

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# цикл жизни приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    yield


app = FastAPI(
    title="prod/polygon API",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://185.50.202.253:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# эндпоинт для проверки работоспособности сервера
@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}