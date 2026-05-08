"""
Repository xử lý truy xuất và cập nhật bảng sticks.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.relationship import Relationship
from models.stick import Stick


async def get_stick_by_id(db: AsyncSession, stick_id: str) -> Optional[Stick]:
    """Tìm một cây gậy theo ID."""
    result = await db.execute(select(Stick).where(Stick.stick_id == stick_id))
    return result.scalar_one_or_none()


async def update_stick_owner(db: AsyncSession, stick_id: str, owner_id: int) -> Stick:
    """
    Cập nhật chủ sở hữu của gậy.
    Nếu gậy chưa tồn tại trong DB, tự động tạo mới gậy đó rồi gán owner_id luôn.
    """
    stick = await get_stick_by_id(db, stick_id)
    if not stick:
        stick = Stick(stick_id=stick_id, owner_id=owner_id, status="online")
        db.add(stick)
    else:
        stick.owner_id = owner_id

    await db.commit()
    await db.refresh(stick)
    return stick


async def get_stick_by_owner(db: AsyncSession, owner_id: int) -> Optional[Stick]:
    """Lấy gậy theo ID của người khiếm thị (owner)."""
    result = await db.execute(select(Stick).where(Stick.owner_id == owner_id))
    # Trả về gậy đầu tiên tìm thấy (giả định mỗi người khiếm thị dùng 1 gậy)
    return result.scalars().first()


async def get_sticks_by_caretaker(db: AsyncSession, caretaker_id: int) -> list[Stick]:
    """Lấy danh sách gậy của những người khiếm thị mà caretaker này đang theo dõi."""
    # Join bảng Relationship và bảng Stick:
    # Lấy ra các Stick mà Stick.owner_id trùng với Relationship.blind_user_id
    # với điều kiện Relationship.caretaker_id == caretaker_id
    stmt = (
        select(Stick)
        .join(Relationship, Stick.owner_id == Relationship.blind_user_id)
        .where(Relationship.caretaker_id == caretaker_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
