from app.db.base import Base, engine
from app.db import models

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database not available yet (will connect in Docker): {e}")
        print("Continuing without database connection...")