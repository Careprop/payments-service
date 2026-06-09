from fastapi import Header
from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.config import settings


async def validate_api_key(
    x_api_key: str = Header(),
):
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
