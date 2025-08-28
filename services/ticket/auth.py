import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import httpx
import schemas
import logging

logger = logging.getLogger("ticket.auth")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

# JWT Configuration (should match gateway service)
SECRET_KEY_DEFAULT = "a_very_secret_key_that_should_be_changed"
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY_DEFAULT)
if SECRET_KEY == SECRET_KEY_DEFAULT:
    logger.warning("Using default SECRET_KEY in ticket service. Set a strong SECRET_KEY in environment.")
ALGORITHM = "HS256"
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")

# tokenUrl should point to gateway's token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Shared HTTP client (lazy)
_http_client: httpx.AsyncClient | None = None

async def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=10.0)
    return _http_client

async def get_current_user_from_gateway(token: str) -> Optional[schemas.CurrentUser]:
    """Get current user info from gateway service"""
    try:
        client = await _get_client()
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{GATEWAY_URL}/users/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            return schemas.CurrentUser(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"]
            )
        if response.status_code >= 500:
            logger.error("Gateway user lookup error %s", response.status_code)
        return None
    except Exception as e:
        logger.exception("Error getting user from gateway: %s", e)
        return None

def verify_token_locally(token: str) -> Optional[dict]:
    """Verify JWT token locally (fallback method)"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            return None
        return {"username": username, "role": role}
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> schemas.CurrentUser:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = await get_current_user_from_gateway(token)
    if user:
        return user
    token_data = verify_token_locally(token)
    if token_data:
        return schemas.CurrentUser(
            id=0,
            username=token_data["username"],
            email="",
            role=token_data["role"]
        )
    raise credentials_exception

async def get_current_admin_user(current_user: schemas.CurrentUser = Depends(get_current_user)) -> schemas.CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> Optional[schemas.CurrentUser]:
    try:
        return await get_current_user(token)
    except HTTPException:
        return None