from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings, Settings

settings: Settings = get_settings()

#Create async engine for FastAPI
engine: AsyncEngine = create_async_engine(
  str(settings.database.url),
  pool_size= settings.database.pool_size,
  max_overflow= settings.database.max_overflow,
  pool_pre_ping=True
)

# Create async session of db
AsyncSessionLocal = async_sessionmaker(
  bind=engine,
  class_=AsyncSession,
  expire_on_commit=False,
  autoflush=False,
  autocommit=False
)

