import datetime
import hashlib
import hmac

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models import AuditLog, User
from backend.app.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def hash_device_token(token: str) -> str:
    """Generate SHA-256 hash for stored device pre-shared tokens"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_device_token(provided_token: str, stored_hash: str) -> bool:
    """Constant-time comparison against timing attacks"""
    if not provided_token or not stored_hash:
        return False
    calculated = hashlib.sha256(provided_token.encode('utf-8')).hexdigest()
    return hmac.compare_digest(calculated, stored_hash)


def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")
    return user


def require_role(allowed_roles: list[str]):
    """
    Factory for RBAC route protection.
    Enforces authorization at the backend level.
    Logs unauthorized access attempts into the audit log.
    """
    def role_checker(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if current_user.role not in allowed_roles:
            # Audit log the unauthorized attempt
            client_ip = request.client.host if request.client else "unknown"
            audit_entry = AuditLog(
                event_type="UNAUTHORIZED_ACCESS",
                actor_type="USER",
                actor_id=current_user.username,
                action=f"{request.method} {request.url.path}",
                resource=str(request.url.path),
                result="BLOCKED",
                severity="WARNING",
                ip_address=client_ip,
                details=f"User role '{current_user.role}' attempted action requiring roles: {allowed_roles}"
            )
            db.add(audit_entry)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges. Required role: {allowed_roles}"
            )
        return current_user

    return role_checker
