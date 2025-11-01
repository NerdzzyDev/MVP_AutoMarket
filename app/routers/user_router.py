# app/routers/user_router.py
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db as get_db
from app.schemas.user_schema import GoogleLogin, Token, UserLogin, UserRegister, UserResponse, UserUpdate
from app.services.user_service import UserService

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])


# JWT utils
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Current user dependency
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await UserService.get_user_by_email(db, email)
    if not user:
        raise credentials_exception
    return user


# --- REGISTER ---
@router.post("/register", response_model=UserResponse)
async def register(
    email: str = Form(...),
    password: str = Form(...),
    vin: str | None = Form(None),
    brand: str | None = Form(None),
    model: str | None = Form(None),
    engine: str | None = Form(None),
    kba_code: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    # Валидация через Pydantic
    try:
        user_data = UserRegister(
            email=email,
            password=password,
            vin=vin,
            brand=brand,
            model=model,
            engine=engine,
            kba_code=kba_code,
        )
    except ValidationError as e:
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in e.errors()]
        raise HTTPException(status_code=400, detail=errors)

    # Проверка на существующего пользователя
    if await UserService.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email is already registered")

    try:
        user = await UserService.create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return user


# --- LOGIN ---
@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await UserService.authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user.email})
    return Token(access_token=token)


# --- GOOGLE LOGIN ---
@router.post("/login/google", response_model=Token)
async def google_login(google_data: GoogleLogin, db: AsyncSession = Depends(get_db)):
    try:
        payload = id_token.verify_oauth2_token(google_data.id_token, google_requests.Request())
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google token invalid: email missing")
    except ValueError:
        raise HTTPException(status_code=400, detail="Google token invalid")

    user = await UserService.create_or_get_google_user(db, email)
    token = create_access_token({"sub": user.email})
    return Token(access_token=token)


# --- GET ME ---
@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


# --- UPDATE ME ---
@router.patch("/users/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        user = await UserService.update_user(db, current_user, update_data)
    except ValidationError as e:
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in e.errors()]
        raise HTTPException(status_code=400, detail=errors)

    return user
