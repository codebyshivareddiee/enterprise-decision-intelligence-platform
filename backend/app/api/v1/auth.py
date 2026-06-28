"""Authentication API Endpoints."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.models import User
from app.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    Token,
    UserResponse,
)
from app.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request_data: RegisterRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    req_id = request.headers.get("X-Request-ID", "")
    user = await auth_service.register(request_data, req_id=req_id)
    return UserResponse.model_validate(user.model_dump())


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    req_id = request.headers.get("X-Request-ID", "")
    # Map OAuth2PasswordRequestForm.username to email
    login_req = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login(login_req, req_id=req_id)


@router.post("/refresh", response_model=Token)
async def refresh(
    request_data: RefreshRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    req_id = request.headers.get("X-Request-ID", "")
    return await auth_service.refresh(request_data.refresh_token, req_id=req_id)


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout endpoint.
    
    Since we use stateless JWTs, the client simply discards the token.
    A full implementation could add the token to a Redis blocklist here.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user.model_dump())


@router.post("/change-password")
async def change_password(
    request_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    req_id = request.headers.get("X-Request-ID", "")
    await auth_service.change_password(current_user.id, request_data, req_id=req_id)
    return {"message": "Password changed successfully"}
