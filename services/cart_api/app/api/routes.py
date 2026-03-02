from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.cart import CartCreate, CartItemCreate, CartItemRead, CartRead
from app.services.cart_service import add_item, create_cart

router = APIRouter(prefix="/carts", tags=["carts"])


@router.post("", response_model=CartRead)
def create_cart_endpoint(payload: CartCreate, db: Session = Depends(get_db)):
    cart = create_cart(db, payload.user_external_id)
    return CartRead(cart_id=cart.id, total_amount=cart.total_amount, items=[])


@router.post("/{cart_id}/items", response_model=CartRead)
def add_item_endpoint(
    cart_id: int, payload: CartItemCreate, db: Session = Depends(get_db)
):
    try:
        cart = add_item(db, cart_id, payload)
    except AttributeError as exc:
        raise HTTPException(status_code=404, detail="Cart not found") from exc
    return CartRead(
        cart_id=cart.id,
        total_amount=cart.total_amount,
        items=[
            CartItemRead(
                product_id=i.product_id,
                title=i.title,
                qty=i.qty,
                unit_price=i.unit_price,
            )
            for i in cart.items
        ],
    )
