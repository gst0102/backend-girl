from app.database import async_session
from app.services.push_service import process_pending_pushes as _process_pending_pushes


async def process_pending_pushes():
    async with async_session() as db:
        await _process_pending_pushes(db, limit=100)
        await db.commit()