import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    print("Starting migration...")
    async with engine.begin() as conn:
        print("Checking if columns exist...")
        
        # We handle failures gracefully in case columns already exist or phone doesn't exist
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN class_name VARCHAR(50)"))
            print("Added class_name")
        except Exception as e:
            print(f"Skipped class_name: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN roll_no VARCHAR(50)"))
            print("Added roll_no")
        except Exception as e:
            print(f"Skipped roll_no: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN admission_no VARCHAR(50)"))
            print("Added admission_no")
        except Exception as e:
            print(f"Skipped admission_no: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN mobile_numbers JSON"))
            print("Added mobile_numbers")
        except Exception as e:
            print(f"Skipped mobile_numbers: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE students DROP COLUMN phone"))
            print("Dropped phone")
        except Exception as e:
            print(f"Skipped dropping phone: {e}")
            
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
