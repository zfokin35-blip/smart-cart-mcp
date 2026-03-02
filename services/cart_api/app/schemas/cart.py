from pydantic import BaseModel


class CartItemCreate(BaseModel):
    product_id: str
    title: str
    qty: int
    unit_price: float


class CartCreate(BaseModel):
    user_external_id: str


class CartItemRead(BaseModel):
    product_id: str
    title: str
    qty: int
    unit_price: float


class CartRead(BaseModel):
    cart_id: int
    total_amount: float
    items: list[CartItemRead]
