"""
Security and authentication utilities.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer

from core.database import get_db
from models.user import User
from repositories.user_repo import get_user_by_email

# Tạm thời dùng OAuth2PasswordBearer để lấy token (trong tương lai có thể là JWT)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Hàm lấy thông tin user hiện tại đang đăng nhập.
    Lưu ý: Đây là bản mock tạm thời (giả định token chính là email của user để dễ demo).
    Bạn cần thay thế bằng JWT decode logic thực tế.
    """
    if not token:
        # Tạm thời throw lỗi nếu không có token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy token xác thực",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Giả lập: coi token là email để dễ test bằng cách truyền `Bearer test@gmail.com`
    # Thực tế: email = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
    email = token
    
    user = await get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc user không tồn tại",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user
