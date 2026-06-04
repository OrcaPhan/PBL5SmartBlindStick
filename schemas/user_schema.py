from pydantic import BaseModel, EmailStr, Field

class StickLinkIn(BaseModel):
    stick_id: str = Field(..., description="Mã của gậy thông minh")

class CaretakerLinkIn(BaseModel):
    blind_user_email: EmailStr = Field(..., description="Email của người khiếm thị")
