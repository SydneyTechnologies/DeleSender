from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import uuid4, UUID

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
    delivered_date: str = Field(default=str(datetime.now().date))

class Order(BaseModel):
    tracking_id: str = Field(default=str(uuid4()))
    owner_email: str 
    description: str | None 
    status: OrderState = Field(default=OrderState.ordered)
    date: str = Field(default=str(datetime.now().date))
    delivered_date: str | None = Field(default=None)
    order_history: list[str] | None = Field(default=None)


