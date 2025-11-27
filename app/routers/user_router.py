# app/routers/user_router.py
from datetime import UTC, datetime, timedelta
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db as get_db
from app.schemas.user_schema import GoogleLogin, Token, UserRegister, UserResponse
from app.services.user_service import UserService

SECRET_KEY = "your-secret-key"
REFRESH_SECRET_KEY = "your-refresh-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])

# JWT utils
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

# Current user dependency
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
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
    email: str = Form(..., example=""),
    password: str = Form(..., example=""),
    vin: str = Form(""),
    brand: str = Form(""),
    model: str = Form(""),
    engine: str = Form(""),
    kba_code: str = Form(""),
    search_code: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_data = UserRegister(
            email=email,
            password=password,
            vin=vin,
            brand=brand,
            model=model,
            engine=engine,
            kba_code=kba_code,
            search_code=search_code,
        )
    except ValidationError as e:
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in e.errors()]
        raise HTTPException(status_code=400, detail=errors)

    # Проверка на существующего пользователя
    if await UserService.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email is already registered")

    try:
        user = await UserService.create_user(db, user_data)
        await db.refresh(user, attribute_names=["vehicles"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return user

# --- LOGIN ---
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

# --- REFRESH TOKEN ---
@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Проверяем, что пользователь все еще существует
    user = await UserService.get_user_by_email(db, email)
    if not user:
        raise credentials_exception

    # Создаем новые токены
    new_access_token = create_access_token({"sub": user.email})
    new_refresh_token = create_refresh_token({"sub": user.email})
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )

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
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

# --- GET ME ---
@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user

# --- UPDATE ME ---


# --- UPDATE ME ---
@router.patch("/me", response_model=UserResponse)
async def update_me(
    email: str = Form(None),
    password: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Собираем только email и password, остальные поля игнорируем
    update_data = {}
    
    if email is not None:
        email = email.strip()
        if email and email != current_user.email:
            # Проверяем что новый email не занят
            existing_user = await UserService.get_user_by_email(db, email)
            if existing_user:
                raise HTTPException(
                    status_code=400, 
                    detail="Email is already registered by another user"
                )
            update_data["email"] = email
        elif not email:
            raise HTTPException(
                status_code=400,
                detail="Email cannot be empty"
            )
    
    if password is not None:
        password = password.strip()
        if password:
            update_data["password"] = password
        else:
            raise HTTPException(
                status_code=400,
                detail="Password cannot be empty"
            )

    if not update_data:
        raise HTTPException(
            status_code=400, 
            detail="No valid fields to update. Only email and password can be modified"
        )

    user = await UserService.update_user(db, current_user, update_data)
    await db.refresh(user, attribute_names=["vehicles"])

    return user
