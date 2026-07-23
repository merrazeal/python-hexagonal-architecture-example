from faststream.rabbit import RabbitExchange, RabbitQueue
from faststream.rabbit.schemas import ExchangeType

PAYMENTS_EXCHANGE = RabbitExchange(
    name="payments.exchange",
    type=ExchangeType.DIRECT,
    durable=True,
)

PAYMENTS_NEW_QUEUE = "payments.new"

PAYMENTS_QUEUE = RabbitQueue(
    name=PAYMENTS_NEW_QUEUE,
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.dead",
    },
)

PAYMENTS_DLX = RabbitExchange(
    name="payments.dlx",
    type=ExchangeType.DIRECT,
    durable=True,
)

PAYMENTS_DEAD_QUEUE = RabbitQueue(
    name="payments.dead",
    durable=True,
)

PAYMENTS_DISPATCH_QUEUE_NAME = "payments.dispatch"

PAYMENTS_DISPATCH_QUEUE = RabbitQueue(
    name=PAYMENTS_DISPATCH_QUEUE_NAME,
    durable=True,
)
