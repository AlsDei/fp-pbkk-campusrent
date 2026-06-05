"""
FastAPI dependencies: database session, current user extraction, and role guards.
"""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from campusrent.app.database import SessionLocal
from campusrent.app.auth import decode_token
from campusrent.app.models import User, UserStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the current user from a JWT bearer token.

    Raises:
        HTTPException 401: if the token is invalid, expired, or user not found.
        HTTPException 403: if the user is blacklisted or suspended.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: int = payload["sub"]
    except (JWTError, KeyError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if user.status in (UserStatus.BLACKLISTED, UserStatus.SUSPENDED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or blacklisted",
        )

    return user


def require_role(*roles: str):
    """
    Dependency factory that checks if the current user has one of the allowed roles.

    Usage:
        @router.get("/admin/resource", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint(...): ...

    Or as a parameter dependency:
        current_user: User = Depends(require_role("admin", "pemilik_toko"))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles and current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
