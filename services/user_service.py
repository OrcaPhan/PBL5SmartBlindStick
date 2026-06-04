"""
Service xử lý các nghiệp vụ liên kết người dùng và gậy.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.stick_repo import get_stick_by_owner, get_sticks_by_caretaker, update_stick_owner
from repositories.user_repo import create_relationship, get_blind_users_by_caretaker, get_user_by_email


async def link_stick_to_user(db: AsyncSession, current_user: User, stick_id: str) -> dict:
    """
    Liên kết một gậy thông minh với người khiếm thị.
    """
    if current_user.role != "blind_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người dùng khiếm thị (blind_user) mới có thể nhận gậy."
        )

    # Cập nhật hoặc tạo mới gậy với owner_id là current_user
    stick = await update_stick_owner(db=db, stick_id=stick_id, owner_id=current_user.id)
    
    return {
        "message": "Liên kết gậy thành công",
        "stick_id": stick.stick_id,
        "owner_id": stick.owner_id
    }


async def link_caretaker_to_blind_user(db: AsyncSession, current_user: User, blind_user_email: str) -> dict:
    """
    Liên kết tài khoản người nhà (caretaker) với người khiếm thị (blind_user) qua email.
    """
    if current_user.role != "caretaker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người nhà (caretaker) mới có quyền yêu cầu liên kết với người khiếm thị."
        )

    blind_user = await get_user_by_email(db, email=blind_user_email)
    
    if not blind_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng nào với email {blind_user_email}"
        )
        
    if blind_user.role != "blind_user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Người dùng được liên kết không phải là người khiếm thị."
        )

    # Lưu vào bảng relationships
    await create_relationship(
        db=db, 
        caretaker_id=current_user.id, 
        blind_user_id=blind_user.id
    )

    return {
        "message": "Liên kết tài khoản thành công",
        "caretaker_email": current_user.email,
        "blind_user_email": blind_user.email
    }


async def get_my_stick_info(db: AsyncSession, current_user: User) -> dict:
    """
    Lấy thông tin mã gậy dựa vào role của user.
    - Nếu là blind_user: trả về gậy của chính họ.
    - Nếu là caretaker: trả về gậy đầu tiên của người khiếm thị mà họ đang theo dõi (nếu có).
    """
    stick_id = None

    if current_user.role == "blind_user":
        stick = await get_stick_by_owner(db, current_user.id)
        if stick:
            stick_id = stick.stick_id
    elif current_user.role == "caretaker":
        sticks = await get_sticks_by_caretaker(db, current_user.id)
        if sticks:
            # Lấy mã gậy đầu tiên tìm thấy
            stick_id = sticks[0].stick_id

    return {
        "role": current_user.role,
        "stick_id": stick_id
    }


async def get_my_blind_users(db: AsyncSession, current_user: User) -> list[User]:
    """
    Lấy danh sách thông tin người khiếm thị mà người nhà đang theo dõi.
    """
    if current_user.role != "caretaker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người nhà (caretaker) mới có quyền lấy danh sách người khiếm thị."
        )

    return await get_blind_users_by_caretaker(db, caretaker_id=current_user.id)
