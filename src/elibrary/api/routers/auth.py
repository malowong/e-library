from fastapi import APIRouter, status

from elibrary import security
from elibrary.api.deps import AuthServiceDep, SettingsDep
from elibrary.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, auth: AuthServiceDep) -> UserResponse:
    user = await auth.register(payload.email, payload.password)
    return UserResponse.of(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, auth: AuthServiceDep, settings: SettingsDep
) -> TokenResponse:
    user = await auth.authenticate(payload.email, payload.password)
    return TokenResponse(access_token=security.create_access_token(user.id, settings))
