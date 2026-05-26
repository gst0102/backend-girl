import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.kdocs_fetcher import KDOCS_SOURCES
from app.services.kdocs_sync_service import sync_anime_data
from app.tasks.kdocs_tasks import sync_kdocs_data

labels = [s["label"] for s in KDOCS_SOURCES]
print(f"kdocs_fetcher OK - 3 data sources: {labels}")
print("kdocs_sync_service OK")
print("kdocs_tasks OK")

from app.tasks.scheduler import start_scheduler, shutdown_scheduler
print("scheduler OK")