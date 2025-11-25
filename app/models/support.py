# models/support.py
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    subject = Column(String(255), nullable=False)
    status = Column(String(64), default="open")  # open / in_progress / resolved / closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="tickets", lazy="selectin")
    messages = relationship(
        "SupportMessage",
        back_populates="ticket",
        lazy="selectin",  # ✅ async-safe
        cascade="all, delete-orphan"
    )

class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"))
    sender = Column(String(32), nullable=False)  # user / agent / operator
    message = Column(Text, nullable=True)
    attachment_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("SupportTicket", back_populates="messages", lazy="selectin")