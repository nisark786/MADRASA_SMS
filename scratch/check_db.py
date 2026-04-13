import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    url = "postgresql+asyncpg://postgres.esoqzyjrygfqrglouyjt:ChvXaRq9lCNzdNwp@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in res]
        print(f"TABLES_FOUND: {tables}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
