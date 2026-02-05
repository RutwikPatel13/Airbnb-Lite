from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    - **email**: User's email address (must be unique)
    - **password**: User's password (min 6 characters)
    - **name**: User's full name
    - **phone**: Optional phone number
    - **role**: User role (GUEST, HOTEL_ADMIN, ADMIN)
    """
    auth_service = AuthService(db)
    user = await auth_service.signup(request)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and get access tokens.

    Returns access_token and refresh_token for authenticated requests.
    """
    auth_service = AuthService(db)
    return await auth_service.login(request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Use this endpoint when the access token expires to get a new pair of tokens.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_token(request.refresh_token)
