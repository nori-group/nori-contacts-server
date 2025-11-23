from enum import Enum
from uuid import UUID
from pydantic import BaseModel


class PlatformEnum(str, Enum):
    TELEGRAM = "Telegram"
    DISCORD = "Discord"
    MATRIX = "Matrix"


class ContactCard(BaseModel):
    id: UUID
    contact_name: str
    nickname: str | None = None
    contact_avatar_url: str | None = None
    default_platform_contact_id: UUID | None = None


class PlatformContact(BaseModel):
    id: UUID
    contact_card_id: UUID
    platform: PlatformEnum
    platform_user_id: str
    dm_room_id: str
