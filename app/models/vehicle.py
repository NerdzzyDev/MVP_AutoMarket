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
    is_selected = Column(Boolean, default=False)  # <- новое поле

    user = relationship("User", back_populates="vehicles")
