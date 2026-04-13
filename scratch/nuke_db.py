import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def nuke():
    # Using the provided Supabase URL and disabling statement cache for pgBouncer compatibility
    url = "postgresql+asyncpg://postgres.esoqzyjrygfqrglouyjt:ChvXaRq9lCNzdNwp@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
    engine = create_async_engine(url, connect_args={"statement_cache_size": 0})
    
    async with engine.begin() as conn:
        print("ACTION: Dropping public schema...")
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        print("ACTION: Recreating public schema...")
        await conn.execute(text("CREATE SCHEMA public;"))
        print("ACTION: Fixing permissions...")
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        print("STATUS: Database is now completely EMPTY.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(nuke())
