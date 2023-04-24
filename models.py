from pydantic import BaseModel, Field
from datetime import datetime
import enum

class OrderState(str, enum):
    ordered = "ordered"
    shipped = "shipped"
    out_for_delivery = "Out for delivery"
    delivered = "delivered"

class CreateOrderModel(BaseModel):
    trackingId: str
    description: str | None 
    status: OrderState = Field(default=OrderState.ordered)
    date: Field(default=datetime.now())

class UpdateOrderStatusModel(BaseModel):
    status: OrderState = Field(default=OrderState.ordered)
    delivered_date: Field(default=datetime.now())

class Order(BaseModel):
    trackingId: str
    description: str | None 
    status: OrderState
    date: str
    delivered_date: str


