
import tg.settings as settings


def init(channel):
    channel.queue_declare(
        queue = settings.rabbitmq.queue_name,
        durable = True,
    )

    channel.exchange_declare(
        exchange = settings.rabbitmq.exchange_name,
        durable = True,
        exchange_type = 'direct',
    )

    channel.queue_bind(
        queue = settings.rabbitmq.queue_name,
        exchange = settings.rabbitmq.exchange_name,
        routing_key = settings.rabbitmq.routing_key,
    )