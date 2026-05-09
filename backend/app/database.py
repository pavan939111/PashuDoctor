from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.config import settings

# For SQLite, the URL must start with sqlite+aiosqlite://
DATABASE_URL = f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Import models here AFTER Base is defined/imported to register them with Base.metadata
from app.models.user import User
from app.models.case import Case, ChatMessage

async def get_db():
    async with async_session() as session:
        yield session

async def create_db_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
