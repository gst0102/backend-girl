import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session
from app.services.push_service import process_pending_pushes

async def main():
    print("开始处理待发送推送...")
    async with async_session() as db:
        await process_pending_pushes(db, limit=100)
    print("推送处理完成！")

asyncio.run(main())