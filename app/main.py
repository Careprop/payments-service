from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.payments import router
from app.core.migrations import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router, prefix="/api/v1")