from datetime import datetime

from pydantic import BaseModel


class SupportMessageBase(BaseModel):
    sender: str
    message: str | None = None
    attachment_url: str | None = None


class SupportMessageCreate(SupportMessageBase):
    pass


class SupportMessageRead(SupportMessageBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class SupportTicketBase(BaseModel):
    subject: str


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketRead(SupportTicketBase):
    id: int
    status: str
    created_at: datetime
    messages: list[SupportMessageRead] = []

    class Config:
        orm_mode = True
