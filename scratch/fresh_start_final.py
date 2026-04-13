import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
import app.models # Import all models

async def create_fresh():
    # Using the provided Supabase URL and disabling statement cache
    url = "postgresql+asyncpg://postgres.esoqzyjrygfqrglouyjt:ChvXaRq9lCNzdNwp@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
    engine = create_async_engine(url, connect_args={"statement_cache_size": 0})
    
    async with engine.begin() as conn:
        print("ACTION: Dropping EVERYTHING...")
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        
        print("ACTION: Creating all tables via SQLAlchemy...")
        # Since create_all is sync, we use run_sync
        await conn.run_sync(Base.metadata.create_all)
        print("STATUS: All tables created successfully.")
    
    await engine.dispose()

from sqlalchemy import text

if __name__ == "__main__":
    asyncio.run(create_fresh())
