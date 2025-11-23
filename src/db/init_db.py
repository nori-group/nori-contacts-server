import asyncpg


async def create_contact_cards_table(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS contact_cards (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            owner_matrix_id VARCHAR NOT NULL,
            contact_name VARCHAR NOT NULL,
            nickname VARCHAR,
            contact_avatar_url VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_owner_matrix_id ON contact_cards(owner_matrix_id);
    """)
    print("contact_cards table checked/created.")


async def create_platform_contacts_table(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS platform_contacts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            contact_card_id UUID NOT NULL REFERENCES contact_cards (id) ON DELETE CASCADE,
            platform VARCHAR NOT NULL,
            platform_user_id VARCHAR NOT NULL,
            dm_room_id VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (contact_card_id, platform, platform_user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_platform_user_id ON platform_contacts(platform_user_id);
    """)
    print("platform_contacts table checked/created.")


async def create_all_tables(conn: asyncpg.Connection):
    await create_contact_cards_table(conn)
    await create_platform_contacts_table(conn)
    
    # Add foreign key after both tables exist to avoid circular dependency
    await conn.execute("""
        ALTER TABLE contact_cards 
        ADD COLUMN IF NOT EXISTS default_platform_contact_id UUID;
        
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_default_platform_contact'
            ) THEN
                ALTER TABLE contact_cards 
                ADD CONSTRAINT fk_default_platform_contact 
                FOREIGN KEY (default_platform_contact_id) 
                REFERENCES platform_contacts(id) 
                ON DELETE SET NULL;
            END IF;
        END $$;
    """)
    print("contact_cards foreign key checked/added.")
