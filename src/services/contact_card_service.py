from uuid import UUID
import asyncpg
from fastapi import HTTPException, status
from schemas.contact_card import ContactCardCreate, ContactCardUpdate
from db.repositories.contact_cards_repository import (
    get_contact_cards_by_owner,
    insert_contact_card,
    update_contact_card as update_contact_card_in_db,
    delete_contact_card as delete_contact_card_in_db,
    get_single_contact_card_by_id_and_owner,
)


class ContactCardServicer:
    async def get_all_contact_cards(self, db: asyncpg.Connection, user_id: str):
        return await get_contact_cards_by_owner(db, user_id)

    async def create_contact_card(
        self, db: asyncpg.Connection, user_id: str, contact: ContactCardCreate
    ):
        return await insert_contact_card(
            db,
            user_id,
            contact.contact_name,
            contact.nickname,
            contact.contact_avatar_url,
            contact.default_platform_contact_id,
        )

    async def update_contact_card(
        self,
        db: asyncpg.Connection,
        user_id: str,
        contact_card_id: UUID,
        contact: ContactCardUpdate,
    ):
        record = await get_single_contact_card_by_id_and_owner(
            db, contact_card_id, user_id
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contact card not found."
            )
        updated_contact_card = await update_contact_card_in_db(
            db,
            contact_card_id,
            contact.contact_name,
            contact.nickname,
            contact.contact_avatar_url,
            contact.default_platform_contact_id,
        )
        if updated_contact_card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contact card not found."
            )
        return updated_contact_card

    async def delete_contact_card(
        self, db: asyncpg.Connection, user_id: str, contact_card_id: UUID
    ):
        record = await get_single_contact_card_by_id_and_owner(
            db, contact_card_id, user_id
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contact card not found."
            )
        await delete_contact_card_in_db(
            db,
            contact_card_id,
        )
