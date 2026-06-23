from pydantic import BaseModel, Field
from enum import Enum
import uuid


class StatusPedido(str, Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"


class PedidoCreate(BaseModel):
    nome_cliente: str
    nome_produto: str
    quantidade: int


class Pedido(PedidoCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: StatusPedido = StatusPedido.PENDENTE