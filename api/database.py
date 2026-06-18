import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


engine = create_async_engine(
    os.environ["DATABASE_URL"],
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass



async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from api.models import User, ConversationSession, ConversationMessage, AgentTransition, SessionUserData, CheckoutRecord
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)