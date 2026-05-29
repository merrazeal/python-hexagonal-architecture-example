import logging
import queue
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from src.boot.test.di import get_container
from src.config import settings
from src.handlers.api.rest.v1.payment.routes import router as payment_router
from src.handlers.api.rest.v1.system.routes import router as system_router
from src.log_config import (create_console_handler, setup_queue_logger,
                            start_queue_listener)

container = get_container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_queue: queue.Queue = queue.Queue(maxsize=settings.log_queue_maxsize)
    setup_queue_logger(log_queue, level=logging.INFO)
    handler = create_console_handler(settings.log_format, logging.INFO)
    queue_listener = start_queue_listener(log_queue, handler)

    yield

    await container.close()
    queue_listener.stop()


app = FastAPI(title="Payment Processing Service", version="1.0.0", lifespan=lifespan)


setup_dishka(container=container, app=app)

app.include_router(system_router)
app.include_router(payment_router)
