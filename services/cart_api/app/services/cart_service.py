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


def get_latest_cart_by_user(db: Session, user_external_id: str) -> models.Cart | None:
    return (
        db.query(models.Cart)
        .join(models.Session, models.Cart.session_id == models.Session.id)
        .join(models.User, models.Session.user_id == models.User.id)
        .filter(models.User.external_id == user_external_id)
        .order_by(models.Cart.id.desc())
        .first()
    )


def clear_cart(db: Session, cart_id: int) -> models.Cart | None:
    cart = db.query(models.Cart).filter_by(id=cart_id).first()
    if not cart:
        return None
    cart.items.clear()
    cart.total_amount = 0
    db.commit()
    db.refresh(cart)
    return cart
