"""Auth router: registration and login endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from campusrent.app.deps import get_db
from campusrent.app.auth import hash_password, verify_password, create_access_token
from campusrent.app.models import User, UserStatus, UserRole
from campusrent.app.schemas import RegisterRequest, RegisterResponse, LoginRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user with email, password, and role.

    - Validates email uniqueness (case-insensitive)
    - Hashes password with bcrypt
    - Creates user with selected role (penyewa or pemilik_toko)
    """
    # Check email uniqueness (case-insensitive)
    existing_user = db.query(User).filter(
        func.lower(User.email) == request.email.lower()
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash the password
    hashed = hash_password(request.password)

    # Create the user
    new_user = User(
        email=request.email.lower(),
        password_hash=hashed,
        role=UserRole(request.role),
        status=UserStatus.ACTIVE,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RegisterResponse(
        id=new_user.id,
        email=new_user.email,
        role=new_user.role.value,
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return a JWT access token.

    - Finds user by email (case-insensitive)
    - Verifies password
    - Rejects suspended/blacklisted users with 403
    - Returns JWT token on success
    """
    # Find user by email (case-insensitive)
    user = db.query(User).filter(
        func.lower(User.email) == request.email.lower()
    ).first()

    # Invalid credentials - don't reveal if email or password was wrong
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check user status - reject suspended/blacklisted
    if user.status in (UserStatus.SUSPENDED, UserStatus.BLACKLISTED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or blacklisted",
        )

    # Create and return JWT token
    access_token = create_access_token(user_id=user.id, role=user.role.value)

    return TokenResponse(access_token=access_token, token_type="bearer")
