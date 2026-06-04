"""
Repository xử lý thông tin và liên kết người dùng.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.relationship import Relationship
from models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Tìm user theo email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_relationship(db: AsyncSession, caretaker_id: int, blind_user_id: int) -> Relationship:
    """Tạo liên kết giữa caretaker và blind_user."""
    # Kiểm tra xem liên kết đã tồn tại chưa
    result = await db.execute(
        select(Relationship).where(
            Relationship.caretaker_id == caretaker_id,
            Relationship.blind_user_id == blind_user_id
        )
    )
    existing_link = result.scalar_one_or_none()
    
    if existing_link:
        return existing_link

    # Thêm mới nếu chưa có
    new_link = Relationship(caretaker_id=caretaker_id, blind_user_id=blind_user_id)
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link


async def get_blind_users_by_caretaker(db: AsyncSession, caretaker_id: int) -> list[User]:
    """Lấy danh sách thông tin người khiếm thị mà người nhà đang theo dõi."""
    stmt = (
        select(User)
        .join(Relationship, User.id == Relationship.blind_user_id)
        .where(Relationship.caretaker_id == caretaker_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
