import asyncio
import logging
import queue as stdlib_queue

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.boot.test.di import get_container
from src.config import settings
from src.handlers.cron.payment import dispatch_payment_events
from src.log_config import (create_console_handler, setup_queue_logger,
                            start_queue_listener)

_log_queue: stdlib_queue.Queue = stdlib_queue.Queue(maxsize=settings.log_queue_maxsize)
setup_queue_logger(_log_queue, level=logging.INFO)
_handler = create_console_handler(settings.log_format, logging.INFO)
_queue_listener = start_queue_listener(_log_queue, _handler)

logger = logging.getLogger(__name__)


async def main() -> None:
    container = get_container()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        dispatch_payment_events,
        IntervalTrigger(seconds=settings.dispatch_interval_seconds),
        id="dispatch_payment_events",
        kwargs={"container": container},
    )
    scheduler.start()
    logger.info("Scheduler started")
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()
        await container.close()
        _queue_listener.stop()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())
