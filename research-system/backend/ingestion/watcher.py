import asyncio
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from backend.config import settings

logger = logging.getLogger(__name__)


class InboxHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        path = Path(str(event.src_path))
        if path.suffix.lower() == ".pdf":
            logger.info("New PDF detected: %s", path)
            # Import here to avoid circular imports at module level
            from backend.ingestion.sources.pdf import ingest_pdf
            asyncio.run_coroutine_threadsafe(ingest_pdf(path), self.loop)


def start_watcher(loop: asyncio.AbstractEventLoop) -> Observer:
    inbox = settings.research_inbox_dir
    inbox.mkdir(parents=True, exist_ok=True)
    handler = InboxHandler(loop)
    observer = Observer()
    observer.schedule(handler, str(inbox), recursive=False)
    observer.start()
    logger.info("Watching %s for new PDFs", inbox)
    return observer
