import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import sys
import logging
sys.path.append('/app')

load_dotenv()

# It's highly recommended to set this in your .env file
# You can generate a secure key with: openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

logger = logging.getLogger("gateway.security")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decodes JWT, validates credentials, and returns the user."""
    import crud, schemas
    from database import get_db, SessionLocal
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = None
    username = None
    try:
        # Log minimal token info (length only)
        if token:
            logger.debug("Auth attempt token_len=%d", len(token))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        exp = payload.get("exp")
        if username is None:
            logger.warning("JWT decode missing sub. payload_keys=%s", list(payload.keys()))
            raise credentials_exception
        logger.debug("JWT decoded sub=%s role=%s exp=%s", username, role, exp)
        token_data = schemas.TokenData(username=username)
    except JWTError as e:
        logger.warning("JWT decode failed: %s", e)
        raise credentials_exception
    
    # Create a new database session
    db = SessionLocal()
    try:
        user = crud.get_user_by_username(db, username=token_data.username)
        if user is None:
            logger.warning("User not found in DB for sub=%s", username)
            raise credentials_exception
        logger.debug("Authenticated user id=%s username=%s role=%s", user.id, user.username, user.role)
        return user
    finally:
        db.close()