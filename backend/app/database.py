from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# For SQLite, the URL must start with sqlite+aiosqlite://
DATABASE_URL = f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session
