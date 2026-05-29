import logging
import queue

from dishka.integrations.faststream import setup_dishka
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitRouter

from src.boot.dev.di import get_container
from src.config import settings
from src.handlers.tasks.v1.payment import v1_payment_handlers
from src.log_config import (create_console_handler, setup_queue_logger,
                            start_queue_listener)

_log_queue: queue.Queue = queue.Queue(maxsize=settings.log_queue_maxsize)
_root_logger = setup_queue_logger(_log_queue, level=logging.INFO)
_handler = create_console_handler(settings.log_format, logging.INFO)
_queue_listener = start_queue_listener(_log_queue, _handler)

router = RabbitRouter(handlers=v1_payment_handlers)

broker = RabbitBroker(settings.rabbitmq_url, logger=_root_logger)
broker.include_router(router)

app = FastStream(broker, logger=_root_logger)

container = get_container()
setup_dishka(container=container, app=app)


@app.after_shutdown
async def close_resources() -> None:
    await container.close()
    _queue_listener.stop()
