from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import schemas, crud
from .config import settings
from .database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет пароль с использованием чистого bcrypt
    """
    try:
        # Кодируем пароль в bytes
        password_bytes = plain_password.encode('utf-8')

        # Если пароль слишком длинный, обрезаем до 72 байтов
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # Проверяем пароль
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль с использованием чистого bcrypt
    """
    # Кодируем пароль в bytes
    password_bytes = password.encode('utf-8')

    # Обрезаем до 72 байтов если нужно
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Генерируем соль и хеш
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Возвращаем как строку
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
