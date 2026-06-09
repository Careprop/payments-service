from fastapi import FastAPI

from app.api.v1.payments import router

app = FastAPI()

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    ...