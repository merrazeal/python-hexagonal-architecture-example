import logging
import queue
import sys
from logging.handlers import QueueHandler, QueueListener


def setup_queue_logger(
    log_queue: queue.Queue, level: int = logging.INFO
) -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(QueueHandler(log_queue))
    return root_logger


def start_queue_listener(
    log_queue: queue.Queue, handler: logging.Handler
) -> QueueListener:
    listener = QueueListener(log_queue, handler)
    listener.start()
    return listener


def create_console_handler(
    log_format: str, level: int = logging.INFO
) -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    handler.setLevel(level)
    return handler
