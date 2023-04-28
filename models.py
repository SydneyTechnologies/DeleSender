from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import uuid4, UUID


def getTrackingId():
    return str(uuid4())

def getDate():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class OrderState(str, Enum):
    ordered = "ordered"
    shipped = "shipped"
    out_for_delivery = "Out for delivery"
    delivered = "delivered"
    cancelled = "cancelled"

class CreateOrderModel(BaseModel):
    owner_email: str 
    description: str | None 

class UpdateOrderStatusModel(BaseModel):
    status: OrderState = Field(default=OrderState.ordered)
    update_message: str | None = Field(default=None)
    delivered_date: str = Field(default_factory=getDate)


class Order(BaseModel):
    tracking_id: str = Field(default_factory=getTrackingId)
    owner_email: str 
    description: str | None 
    status: OrderState = Field(default=OrderState.ordered)
    date: str = Field(default_factory=getDate)
    delivered_date: str | None = Field(default=None)
    order_history: list[str] = []


