"""
Schemas cho API dang ky / dang nhap nguoi dung.
"""

from pydantic import BaseModel, ConfigDict, Field


class UserProfileOut(BaseModel):
    """Thong tin nguoi dung tra ve cho client."""

    id: int
    email: str
    full_name: str | None
    role: str | None
    phone: str | None

    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    """Schema validate request dang ky tai khoan."""

    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str | None = Field(default=None, max_length=100)
    role: str = Field(default="blind_user", pattern="^(blind_user|caretaker)$")
    phone: str | None = Field(default=None, max_length=15)


class RegisterOut(BaseModel):
    """Schema response sau khi dang ky thanh cong."""

    message: str
    user: UserProfileOut


class LoginIn(BaseModel):
    """Schema validate request dang nhap."""

    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class LoginOut(BaseModel):
    """Schema response sau khi dang nhap thanh cong."""

    message: str
    user: UserProfileOut
