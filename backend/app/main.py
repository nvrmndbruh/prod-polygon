from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.models.base import Base
from app.db.db_session import engine

# импортируем все модели до вызова create_all
from app.db import models


# менеджер жизненного цикла приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# экземпляр FastAPI
app = FastAPI(
    title="прод/полигон API",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React App
        "http://localhost:5173",   # Vite
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# маршрут для проверки работоспособности сервера
@app.get("/health", tags=["system"])
async def health():
    # проверка работоспособности сервера
    return {"status": "ok"}