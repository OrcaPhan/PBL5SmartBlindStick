"""
Router cho các API liên kết người dùng và thiết bị.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.auth_schema import UserProfileOut
from schemas.user_schema import CaretakerLinkIn, StickLinkIn
from services.user_service import get_my_blind_users, get_my_stick_info, link_caretaker_to_blind_user, link_stick_to_user

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/link-stick")
async def api_link_stick(
    payload: StickLinkIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Liên kết gậy thông minh với người dùng khiếm thị hiện tại (cần token).
    """
    return await link_stick_to_user(
        db=db, 
        current_user=current_user, 
        stick_id=payload.stick_id
    )


@router.post("/link-caretaker")
async def api_link_caretaker(
    payload: CaretakerLinkIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Liên kết người nhà (caretaker đang đăng nhập) với một người khiếm thị qua email.
    """
    return await link_caretaker_to_blind_user(
        db=db, 
        current_user=current_user, 
        blind_user_email=payload.blind_user_email
    )


@router.get("/my-stick")
async def api_get_my_stick(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy mã gậy (stick_id) mà user hiện tại đang sở hữu (nếu là người khiếm thị)
    hoặc đang theo dõi (nếu là người nhà).
    """
    return await get_my_stick_info(db=db, current_user=current_user)


@router.get("/my-blind-users", response_model=list[UserProfileOut])
async def api_get_my_blind_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy danh sách thông tin người khiếm thị mà người nhà (caretaker) này đang theo dõi.
    (API này chỉ dành riêng cho role caretaker).
    """
    return await get_my_blind_users(db=db, current_user=current_user)
