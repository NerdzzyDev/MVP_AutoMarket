# app/services/user_service.py
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vehicle import Vehicle

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def create_user(db: AsyncSession, user_data):
        if len(user_data.password.encode("utf-8")) > 72:
            raise HTTPException(status_code=400, detail="Password too long (max 72 bytes).")

        hashed_pw = pwd_context.hash(user_data.password)
        user = User(email=user_data.email, password_hash=hashed_pw)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        if user_data.vin:
            vehicle = Vehicle(
                user_id=user.id,
                vin=user_data.vin,
                brand=user_data.brand,
                model=user_data.model,
                engine=user_data.engine,
                kba_code=user_data.kba_code,
            )
            db.add(vehicle)
            await db.commit()
            await db.refresh(vehicle)

        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str):
        user = await UserService.get_user_by_email(db, email)
        if user and pwd_context.verify(password, user.password_hash):
            return user
        return None

    @staticmethod
    async def create_or_get_google_user(db: AsyncSession, email: str):
        user = await UserService.get_user_by_email(db, email)
        if not user:
            user = User(email=email, password_hash="")
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    # -----------------------
    # Новый метод: update_user
    # -----------------------
    @staticmethod
    async def update_user(db: AsyncSession, user: User, update_data):
        """
        Обновляет поля пользователя: full_name, password, email и т.п.
        update_data — Pydantic модель UserUpdate
        """
        updated = False

        if getattr(update_data, "full_name", None):
            user.full_name = update_data.full_name
            updated = True

        if getattr(update_data, "email", None):
            user.email = update_data.email
            updated = True

        if getattr(update_data, "password", None):
            if len(update_data.password.encode("utf-8")) > 72:
                raise HTTPException(status_code=400, detail="Password too long (max 72 bytes).")
            user.password_hash = pwd_context.hash(update_data.password)
            updated = True

        if updated:
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user
