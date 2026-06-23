from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app import messaging as messaging_module

messaging_module.MessagingApp.connect = AsyncMock()
messaging_module.MessagingApp.close = AsyncMock()
messaging_module.MessagingApp.publish_rabbitmq = AsyncMock()
messaging_module.MessagingApp.publish_kafka = AsyncMock()

from app import main as main_module  # noqa: E402
from app.main import app  # noqa: E402

mock_client = AsyncMongoMockClient()
main_module.client = mock_client
main_module.db = mock_client.ecommerce
main_module.colecao_pedidos = mock_client.ecommerce.pedidos


@pytest.fixture(autouse=True)
async def limpar_banco():
    await main_module.colecao_pedidos.delete_many({})
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_criar_pedido(client):
    payload = {"nome_cliente": "João", "nome_produto": "Notebook", "quantidade": 1}
    response = await client.post("/pedidos/", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDENTE"
    assert "id" in body
    assert body["nome_cliente"] == "João"


@pytest.mark.asyncio
async def test_listar_pedidos(client):
    payload = {"nome_cliente": "Maria", "nome_produto": "Mouse", "quantidade": 2}
    await client.post("/pedidos/", json=payload)

    response = await client.get("/pedidos/")

    assert response.status_code == 200
    assert len(response.json()) >= 1