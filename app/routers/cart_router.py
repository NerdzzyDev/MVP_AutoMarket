from fastapi import APIRouter, Depends, Form, HTTPException, Path
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import get_async_db
from app.models.user import CartItem, Product, User
from app.routers.user_router import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/")
async def get_cart(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    try:
        result = await session.execute(select(CartItem).where(CartItem.user_id == user.id))
        items = result.scalars().all()

        logger.info(f"User {user.email} fetched {len(items)} cart items")

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

    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving cart for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while retrieving cart")

    except Exception as e:
        logger.exception(f"Unexpected error in get_cart for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.post("/add")
async def add_to_cart(
    product_id: int = Form(...),
    quantity: int = Form(1),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    try:
        product = await session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        existing = await session.execute(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
        )
        cart_item = existing.scalar_one_or_none()

        if cart_item:
            cart_item.quantity += quantity
            logger.info(f"User {user.email} increased quantity of product {product_id} to {cart_item.quantity}")
        else:
            cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=quantity)
            session.add(cart_item)
            logger.info(f"User {user.email} added product {product_id} (qty={quantity}) to cart")

        await session.commit()
        await session.refresh(cart_item)
        return {"id": cart_item.id, "quantity": cart_item.quantity}

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error while adding product {product_id} for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while adding product to cart")

    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error in add_to_cart for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while adding to cart")


@router.delete("/remove/{id}")
async def remove_from_cart(
    id: int = Path(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    try:
        result = await session.execute(select(CartItem).where(CartItem.id == id, CartItem.user_id == user.id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        await session.delete(item)
        await session.commit()

        logger.info(f"User {user.email} removed cart item {id}")

        return {"message": "Removed from cart"}

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error while removing cart item {id} for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while removing cart item")

    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error in remove_from_cart for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while removing cart item")
