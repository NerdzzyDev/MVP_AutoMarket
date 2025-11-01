# app/models/user.py (Vehicle)
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.db import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    vin = Column(String(64), index=True)
    brand = Column(String(128))
    model = Column(String(128))
    engine = Column(String(128))
    kba_code = Column(String(64))
    search_code = Column(String(128), nullable=True)  # <- новое поле
    is_selected = Column(Boolean, default=False)

    user = relationship("User", back_populates="vehicles")
