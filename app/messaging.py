import json
import os

import aio_pika
from aiokafka import AIOKafkaProducer

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


class MessagingApp:
    def __init__(self):
        self.rmq_connection = None
        self.rmq_channel = None
        self.kafka_producer = None

    async def connect(self):
        self.rmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
        self.rmq_channel = await self.rmq_connection.channel()
        await self.rmq_channel.declare_queue("pedidos_criados", durable=True)

        self.kafka_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self.kafka_producer.start()

    async def close(self):
        if self.rmq_connection:
            await self.rmq_connection.close()
        if self.kafka_producer:
            await self.kafka_producer.stop()

    async def publish_rabbitmq(self, pedido_dict: dict):
        mensagem = aio_pika.Message(body=json.dumps(pedido_dict).encode())
        await self.rmq_channel.default_exchange.publish(
            mensagem, routing_key="pedidos_criados"
        )

    async def publish_kafka(self, pedido_dict: dict):
        await self.kafka_producer.send_and_wait("topico_pedidos", pedido_dict)


messaging = MessagingApp()