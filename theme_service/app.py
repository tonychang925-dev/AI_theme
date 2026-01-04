import asyncio
import logging
from fastapi import FastAPI
from theme_service.scheduler import scheduler_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("theme_service")

app = FastAPI(title="theme_service")

@app.on_event("startup")
async def startup():
    asyncio.create_task(scheduler_loop())
    logger.info("theme_service started")
