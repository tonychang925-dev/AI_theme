import asyncpg
from theme_service.config import DATABASE_URL

async def get_conn():
    return await asyncpg.connect(DATABASE_URL)
