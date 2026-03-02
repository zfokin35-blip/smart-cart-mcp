from sqlalchemy.orm import Session

from app.db import models
from app.schemas.cart import CartItemCreate
from app.services.pricing import recalc_total


def get_or_create_user(db: Session, external_id: str) -> models.User:
    user = db.query(models.User).filter_by(external_id=external_id).first()
    if user:
        return user
    user = models.User(external_id=external_id)
    db.add(user)
    db.flush()
    return user


def create_cart(db: Session, user_external_id: str) -> models.Cart:
    user = get_or_create_user(db, user_external_id)
    session = models.Session(user_id=user.id)
    db.add(session)
    db.flush()
    cart = models.Cart(session_id=session.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def add_item(db: Session, cart_id: int, item_in: CartItemCreate) -> models.Cart:
    cart = db.query(models.Cart).filter_by(id=cart_id).first()
    item = models.CartItem(cart_id=cart.id, **item_in.model_dump())
    db.add(item)
    db.flush()
    cart.total_amount = recalc_total(cart.items)
    db.commit()
    db.refresh(cart)
    return cart
