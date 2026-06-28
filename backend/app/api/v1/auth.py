"""Authentication API Endpoints."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_auth_service, get_audit_repository
from app.auth.dependencies import require_authenticated_user
from app.auth.models import User, AuditEvent
from app.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    Token,
    UserResponse,
)
from app.auth.service import AuthService
from app.api.v1.models.response import StandardResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    request_data: RegisterRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[UserResponse]:
    req_id = getattr(request.state, "request_id", "")
    user = await auth_service.register(request_data, req_id=req_id)
    return StandardResponse(
        success=True,
        data=UserResponse.model_validate(user.model_dump()),
        message="User registered successfully.",
        request_id=req_id,
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    # We do not wrap this in StandardResponse because OAuth2 expects a specific format
    # for Swagger UI authorization to work correctly.
    req_id = getattr(request.state, "request_id", "")
    login_req = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login(login_req, req_id=req_id)


@router.post("/refresh", response_model=Token)
async def refresh(
    request_data: RefreshRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    # Keep OAuth2 standard for refresh token response
    req_id = getattr(request.state, "request_id", "")
    return await auth_service.refresh(request_data.refresh_token, req_id=req_id)


@router.post("/logout", response_model=StandardResponse[dict])
async def logout(
    request: Request,
    audit_repo = Depends(get_audit_repository)
) -> StandardResponse[dict]:
    """Logout endpoint."""
    user_id_str = getattr(request.state, "user_id", None)
    
    await audit_repo.log_event(AuditEvent(
        request_id=getattr(request.state, "request_id", ""),
        user_id=user_id_str,
        action="logout",
        result="success"
    ))
    
    return StandardResponse(
        success=True,
        data={},
        message="Logged out successfully",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_me(
    request: Request,
    current_user: User = Depends(require_authenticated_user())
) -> StandardResponse[UserResponse]:
    return StandardResponse(
        success=True,
        data=UserResponse.model_validate(current_user.model_dump()),
        message="User profile retrieved.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.post("/change-password", response_model=StandardResponse[dict])
async def change_password(
    request_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(require_authenticated_user()),
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[dict]:
    req_id = getattr(request.state, "request_id", "")
    await auth_service.change_password(current_user.id, request_data, req_id=req_id)
    return StandardResponse(
        success=True,
        data={},
        message="Password changed successfully",
        request_id=req_id,
    )
