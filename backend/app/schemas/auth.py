from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class GoogleLoginIn(BaseModel):
    id_token: str = Field(min_length=20, description="ID token dari Google Identity Services")


class DevLoginIn(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    """Bentuk user yang dikirim ke FE. Tidak pernah memuat token/hash apa pun."""

    id: int
    email: str
    name: str
    avatar_url: str | None = None
    role: UserRole

    model_config = {"from_attributes": True}
