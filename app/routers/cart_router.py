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
    title: str = Form(...),
    brand: str = Form(""),
    price: str = Form(""),
    image_url: str = Form(""),
    product_url: str = Form(...),
    delivery_time: str = Form(""),
    description: str = Form(""),
    vin: str | None = Form(None),
    quantity: int = Form(1),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    try:
        # Проверяем — есть ли товар с таким URL
        result = await session.execute(select(Product).where(Product.product_url == product_url))
        product = result.scalar_one_or_none()

        # Если нет — создаём новый товар
        if not product:
            product = Product(
                title=title,
                brand=brand,
                price=price,
                image_url=image_url,
                product_url=product_url,
                delivery_time=delivery_time,
                description=description,
            )
            session.add(product)
            await session.flush()  # чтобы получить ID

        # Проверяем, есть ли уже этот товар в корзине
        existing = await session.execute(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product.id)
        )
        cart_item = existing.scalar_one_or_none()

        if cart_item:
            cart_item.quantity += quantity
            logger.info(f"User {user.email} increased qty for product {product.id} to {cart_item.quantity}")
        else:
            cart_item = CartItem(
                user_id=user.id,
                product_id=product.id,
                quantity=quantity,
                vin=vin,
            )
            session.add(cart_item)
            logger.info(f"User {user.email} added product {product.id} ({product.title}) to cart")

        await session.commit()
        await session.refresh(cart_item)

        return {
            "id": cart_item.id,
            "quantity": cart_item.quantity,
            "product": {
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "product_url": product.product_url,
                "image_url": product.image_url,
                "brand": product.brand,
                "delivery_time": product.delivery_time,
                "description": product.description,
            },
        }

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"DB error while adding product {product_url} for {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while adding to cart")

    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error in add_to_cart for {user.email}: {e}")
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


@router.patch("/decrease/{cart_item_id}")
async def decrease_cart_item_quantity(
    cart_item_id: int = Path(..., description="ID элемента корзины"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    """
    Уменьшает количество товара в корзине на 1.
    Если количество становится 0, удаляет товар из корзины.
    """
    try:
        # Находим элемент корзины пользователя
        result = await session.execute(
            select(CartItem).where(
                CartItem.id == cart_item_id,
                CartItem.user_id == user.id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        # Уменьшаем количество
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            logger.info(f"User {user.email} decreased quantity for cart item {cart_item_id} to {cart_item.quantity}")
            await session.commit()
            await session.refresh(cart_item)
            
            return {
                "message": "Quantity decreased",
                "id": cart_item.id,
                "quantity": cart_item.quantity,
                "removed": False
            }
        else:
            # Если количество было 1, удаляем товар из корзины
            await session.delete(cart_item)
            await session.commit()
            logger.info(f"User {user.email} removed cart item {cart_item_id} (quantity reached 0)")
            
            return {
                "message": "Item removed from cart",
                "id": cart_item_id,
                "quantity": 0,
                "removed": True
            }
            
    except HTTPException:
        raise
        
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error while decreasing quantity for cart item {cart_item_id} for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while updating cart")
        
    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error in decrease_cart_item_quantity for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating cart")


# Дополнительный endpoint для точного установления количества
@router.put("/update/{cart_item_id}")
async def update_cart_item_quantity(
    cart_item_id: int = Path(..., description="ID элемента корзины"),
    quantity: int = Form(..., ge=0, description="Новое количество (0 для удаления)"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    """
    Устанавливает точное количество товара в корзине.
    Если quantity = 0, удаляет товар из корзины.
    """
    try:
        # Находим элемент корзины пользователя
        result = await session.execute(
            select(CartItem).where(
                CartItem.id == cart_item_id,
                CartItem.user_id == user.id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        if quantity == 0:
            # Удаляем товар из корзины
            await session.delete(cart_item)
            await session.commit()
            logger.info(f"User {user.email} removed cart item {cart_item_id} (quantity set to 0)")
            
            return {
                "message": "Item removed from cart",
                "id": cart_item_id,
                "quantity": 0,
                "removed": True
            }
        else:
            # Обновляем количество
            cart_item.quantity = quantity
            await session.commit()
            await session.refresh(cart_item)
            
            logger.info(f"User {user.email} updated quantity for cart item {cart_item_id} to {quantity}")
            
            return {
                "message": "Quantity updated",
                "id": cart_item.id,
                "quantity": cart_item.quantity,
                "removed": False
            }
            
    except HTTPException:
        raise
        
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error while updating quantity for cart item {cart_item_id} for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while updating cart")
        
    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error in update_cart_item_quantity for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating cart")
