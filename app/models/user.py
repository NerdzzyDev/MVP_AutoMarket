from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    is_phantom = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vehicles = relationship(
        "Vehicle",
        back_populates="user",
        lazy="selectin",  # ✅ async-safe загрузка
        cascade="all, delete-orphan",
    )
    favorites = relationship("Favorite", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    tickets = relationship("SupportTicket", back_populates="user", lazy="selectin", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512))
    brand = Column(String(128))
    price = Column(String(64))
    image_url = Column(String(512))
    product_url = Column(String(512))
    delivery_time = Column(String(128))
    description = Column(String)

    favorites = relationship("Favorite", back_populates="product", lazy="selectin", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product", lazy="selectin", cascade="all, delete-orphan")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    vin = Column(String(64), nullable=True)  # Привязка к машине пользователя

    product = relationship("Product")
    user = relationship("User")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    vin = Column(String(64), nullable=True)  # Привязка к машине пользователя
    quantity = Column(Integer, default=1)

    product = relationship("Product")
    user = relationship("User")
