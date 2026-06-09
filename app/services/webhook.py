import asyncio
import httpx


class WebhookService:
    @staticmethod
    async def send(url: str, payload: dict) -> None:
        raise ValueError()
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
            return
