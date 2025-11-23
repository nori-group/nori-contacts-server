from pydantic import BaseModel
from uuid import UUID


class ContactCardResponse(BaseModel):
    id: UUID
    contact_name: str
    nickname: str | None = None
    contact_avatar_url: str | None = None
    default_platform_contact_id: UUID | None = None


class ContactCardCreate(BaseModel):
    contact_name: str
    nickname: str | None = None
    contact_avatar_url: str | None = None
    default_platform_contact_id: UUID | None = None


class ContactCardUpdate(BaseModel):
    contact_name: str
    nickname: str | None = None
    contact_avatar_url: str | None = None
    default_platform_contact_id: UUID | None = None
