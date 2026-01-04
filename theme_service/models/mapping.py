from theme_service.database import get_conn
import logging

logger = logging.getLogger(__name__)

async def create_event_theme_table():
    conn = await get_conn()
    try:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS event_theme_map (
            id SERIAL PRIMARY KEY,
            event_id INT REFERENCES news_event(id),
            theme_id INT REFERENCES theme_master(id),
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT now(),
            UNIQUE(event_id, theme_id)
        );
        """)
        logger.info("event_theme_map table ready")
    finally:
        await conn.close()


async def save_event_theme(event_id, theme_id, confidence, confidence_level=None):
    conn = await get_conn()
    try:
        await conn.execute("""
        INSERT INTO event_theme_map(event_id, theme_id, confidence, confidence_level)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (event_id, theme_id) DO UPDATE
        SET confidence = EXCLUDED.confidence,
            confidence_level = EXCLUDED.confidence_level
        """, event_id, theme_id, confidence, confidence_level)
    finally:
        await conn.close()
