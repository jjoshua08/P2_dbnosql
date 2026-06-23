import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.messaging import messaging
from app.models import Pedido, PedidoCreate

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_URL)
db = client.ecommerce
colecao_pedidos = db.pedidos


@asynccontextmanager
async def lifespan(app: FastAPI):
    await messaging.connect()
    yield
    await messaging.close()
    client.close()


app = FastAPI(title="API de Gerenciamento de Pedidos", lifespan=lifespan)


@app.post("/pedidos/", response_model=Pedido, status_code=201)
async def criar_pedido(pedido_in: PedidoCreate):
    pedido = Pedido(**pedido_in.model_dump())
    pedido_dict = pedido.model_dump()

    #Salva no banco
    await colecao_pedidos.insert_one(pedido_dict.copy())

    #Publica RabbitMQ (informação mínima)
    msg_reduzida = {"id": pedido.id, "status": pedido.status}
    await messaging.publish_rabbitmq(msg_reduzida)

    #Publica Kafka (evento completo)
    await messaging.publish_kafka(pedido_dict)

    return pedido


@app.get("/pedidos/", response_model=List[Pedido])
async def listar_pedidos():
    pedidos_cursor = colecao_pedidos.find({}, {"_id": 0})
    return await pedidos_cursor.to_list(length=1000)