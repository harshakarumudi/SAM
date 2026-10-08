from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.limiter import limiter
from backend.app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from backend.app.models import User
from backend.app.schemas import Token, UserCreate, UserLogin, UserResponse
from backend.app.services.audit_service import log_security_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        log_security_event(
            db=db,
            event_type="AUTH_LOGIN_FAILED",
            actor_type="USER",
            actor_id=login_data.username,
            action="LOGIN",
            resource="/api/auth/login",
            result="FAILURE",
            severity="WARNING",
            ip_address=client_ip,
            details="Invalid username or password"
        )
        # Avoid user enumeration by returning generic authentication error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Generate JWT Token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})

    log_security_event(
        db=db,
        event_type="AUTH_LOGIN_SUCCESS",
        actor_type="USER",
        actor_id=user.username,
        action="LOGIN",
        resource="/api/auth/login",
        result="SUCCESS",
        severity="INFO",
        ip_address=client_ip,
        details=f"User logged in with role {user.role}"
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username
    )


@router.post("/register", response_model=UserResponse)
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    existing = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_security_event(
        db=db,
        event_type="USER_REGISTERED",
        actor_type="USER",
        actor_id=user.username,
        action="REGISTER",
        resource=f"user:{user.id}",
        result="SUCCESS",
        severity="INFO",
        ip_address=client_ip,
        details=f"New user registered with role {user.role}"
    )

    return user


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
