from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import schemas, crud
from .config import settings
from .database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password, hashed_password):
    # Аналогичная обработка для верификации
    password_bytes = plain_password.encode('utf-8')

    # Если пароль длиннее 72 байтов, обрабатываем так же как при хешировании
    if len(password_bytes) > 72:
        import hashlib
        import base64

        password_hash = hashlib.sha256(password_bytes).digest()
        password_str = base64.b64encode(password_hash).decode('utf-8')
        if len(password_str) > 72:
            password_str = password_str[:72]

        return pwd_context.verify(password_str, hashed_password)

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    # Исправление для bcrypt ограничения в 72 байта
    password_bytes = password.encode('utf-8')

    # Если пароль длиннее 72 байтов, обрезаем его
    if len(password_bytes) > 72:
        # Более безопасный подход: хешируем пароль и используем хеш
        import hashlib
        import base64

        # Создаем хеш от полного пароля
        password_hash = hashlib.sha256(password_bytes).digest()
        # Конвертируем в строку base64 (безопаснее чем обрезание UTF-8)
        password_str = base64.b64encode(password_hash).decode('utf-8')
        # Обрезаем до 72 символов
        if len(password_str) > 72:
            password_str = password_str[:72]

        # Используем обрезанный хеш как пароль для bcrypt
        return pwd_context.hash(password_str)

    # Если пароль нормальной длины, используем как есть
    return pwd_context.hash(password)


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
