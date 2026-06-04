"""
Repository thao tac du lieu nguoi dung cho luong xac thuc.
"""

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    """
    Tim nguoi dung theo email.
    """
    stmt: Select[tuple[User]] = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password_hash: str,
    full_name: str | None,
    role: str,
    phone: str | None,
) -> User:
    """
    Tao moi 1 nguoi dung trong bang users.
    """
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        phone=phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
