from fastapi import APIRouter, Depends, Form, HTTPException, Path
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import get_async_db
from app.models.user import Favorite, Product, User
from app.routers.user_router import get_current_user

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/{product_id}")
async def add_favorite(
    product_id: int = Path(...),
    vin: str | None = Form(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    try:
        product = await session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        existing = await session.execute(
            select(Favorite).where(Favorite.user_id == user.id, Favorite.product_id == product_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Already in favorites")

        fav = Favorite(user_id=user.id, product_id=product_id, vin=vin)
        session.add(fav)
        await session.commit()
        await session.refresh(fav)

        logger.info(f"User {user.email} added product {product_id} to favorites (vin={vin})")

        return {
            "id": fav.id,
            "vin": fav.vin,
            "product": {
                "title": product.title,
                "product_url": product.product_url,
                "image_url": product.image_url,
                "price": product.price,
                "seller_name": getattr(product, "seller_name", "N/A"),
                "delivery_time": getattr(product, "delivery_time", None),
                "description": getattr(product, "description", ""),
            },
        }

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error while adding favorite for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while adding to favorites")

    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error in add_favorite for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while adding to favorites")


@router.get("/")
async def list_favorites(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    try:
        result = await session.execute(select(Favorite).where(Favorite.user_id == user.id))
        favorites = result.scalars().all()

        logger.info(f"User {user.email} fetched {len(favorites)} favorite items")

        return [
            {
                "id": f.id,
                "vin": f.vin,
                "product": {
                    "title": f.product.title,
                    "product_url": f.product.product_url,
                    "image_url": f.product.image_url,
                    "price": f.product.price,
                    "seller_name": getattr(f.product, "seller_name", "N/A"),
                    "delivery_time": getattr(f.product, "delivery_time", None),
                    "description": getattr(f.product, "description", ""),
                },
            }
            for f in favorites
        ]

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching favorites for {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching favorites")

    except Exception as e:
        logger.exception(f"Unexpected error in list_favorites for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while retrieving favorites")


@router.delete("/{id}")
async def remove_favorite(
    id: int = Path(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db),
):
    try:
        result = await session.execute(select(Favorite).where(Favorite.id == id, Favorite.user_id == user.id))
        fav = result.scalar_one_or_none()
        if not fav:
            raise HTTPException(status_code=404, detail="Favorite not found")

        await session.delete(fav)
        await session.commit()

        logger.info(f"User {user.email} removed favorite {id}")

        return {"message": "Removed from favorites"}

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error while removing favorite {id} for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Database error while removing favorite")

    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error in remove_favorite for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while removing favorite")
