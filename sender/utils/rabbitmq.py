
class RabbitMQ:
    def __init__(self) -> None:
        self.queue_name = 'messages'
        self.routing_key = 'message'
        self.exchange_name = 'message_exchange'


rabbitmq = RabbitMQ()


def init(channel):
    channel.queue_declare(
        queue = rabbitmq.queue_name,
        durable = True,
    )

    channel.exchange_declare(
        exchange = rabbitmq.exchange_name,
        durable = True,
        exchange_type = 'direct',
    )

    channel.queue_bind(
        queue = rabbitmq.queue_name,
        exchange = rabbitmq.exchange_name,
        routing_key = rabbitmq.routing_key,
    )