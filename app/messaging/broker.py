from faststream.rabbit import RabbitBroker

from app.core.config import settings

broker = RabbitBroker(
    f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}@"
    f"{settings.rabbitmq_host}:{settings.rabbitmq_port}/"
)