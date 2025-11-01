from fastapi import APIRouter, Depends, Form, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import get_async_db
from app.models.user import CartItem, Product, User
from app.routers.user_router import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/")
async def get_cart(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_db)):
    result = await session.execute(select(CartItem).where(CartItem.user_id == user.id))
    items = result.scalars().all()
    return [
        {
            "id": item.id,
            "quantity": item.quantity,
            "product": {
                "title": item.product.title,
                "product_url": item.product.product_url,
                "image_url": item.product.image_url,
                "price": item.product.price,
                "seller_name": getattr(item.product, "seller_name", "N/A"),
                "delivery_time": getattr(item.product, "delivery_time", None),
                "description": getattr(item.product, "description", ""),
            },
        }
        for item in items
    ]


@router.post("/add")
async def add_to_cart(
    product_id: int = Form(...),
    quantity: int = Form(1),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = await session.execute(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    cart_item = existing.scalar_one_or_none()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=quantity)
        session.add(cart_item)

    await session.commit()
    await session.refresh(cart_item)
    return {"id": cart_item.id, "quantity": cart_item.quantity}


@router.delete("/remove/{id}")
async def remove_from_cart(
    id: int = Path(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    result = await session.execute(select(CartItem).where(CartItem.id == id, CartItem.user_id == user.id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    await session.delete(item)
    await session.commit()
    return {"message": "Removed from cart"}
