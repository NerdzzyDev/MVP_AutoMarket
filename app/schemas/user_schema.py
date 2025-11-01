from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    phone: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    password: str | None = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    vin: str | None = None
    brand: str | None = None
    model: str | None = None
    engine: str | None = None
    kba_code: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleLogin(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
