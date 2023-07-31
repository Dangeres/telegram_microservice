
from tg.settings import settings_rabbitmq

import pika

class RabbitMq:
    def __init__(self) -> None:
        self.connection: pika.BlockingConnection = pika.BlockingConnection(
            parameters = pika.URLParameters(
                'amqp://{user}:{password}@{host}:{port}/%2F'.format(
                    **settings_rabbitmq
                )
            )
        )

        self.channel_message: pika.BlockingConnection.channel = self.connection.channel()
    
    