"""
Router cho API dang ky / dang nhap.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.auth_schema import LoginIn, LoginOut, RegisterIn, RegisterOut, UserProfileOut
from services.auth_service import login_user, register_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterIn,
    db: AsyncSession = Depends(get_db),
) -> RegisterOut:
    """
    API dang ky tai khoan moi.
    """
    try:
        user = await register_user(db=db, payload=payload)
        return RegisterOut(
            message="Dang ky thanh cong.",
            user=UserProfileOut.model_validate(user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the dang ky tai khoan.",
        ) from exc


@router.post(
    "/login",
    response_model=LoginOut,
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginIn,
    db: AsyncSession = Depends(get_db),
) -> LoginOut:
    """
    API dang nhap tai khoan.
    """
    try:
        user = await login_user(db=db, payload=payload)
        return LoginOut(
            message="Dang nhap thanh cong.",
            user=UserProfileOut.model_validate(user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the dang nhap tai khoan.",
        ) from exc
