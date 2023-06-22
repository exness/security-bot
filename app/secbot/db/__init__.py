from sqlalchemy import Column, DateTime, event, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.metrics.db.base import get_const_common_labels
from app.metrics.db.sqlalchemy import ConnectionsTotal, add_event_listeners
from app.secbot.settings import settings

engine = create_async_engine(
    settings.postgres_dsn,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,
    pool_size=5,
    pool_recycle=5 * 60,  # 5 minutes
    max_overflow=5,
    pool_timeout=10,
    connect_args={"server_settings": {"jit": "off"}},
    echo=False,
)

# Setup metrics
add_event_listeners(engine)
const_labels = get_const_common_labels(
    db=engine.url.database,
    db_host=engine.url.host,
    db_port=engine.url.port,
)
event.listen(engine.sync_engine, "connect", ConnectionsTotal(const_labels).on_connect)

# Create session factory
db_session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class BaseModel:
    """General model of all models in the project"""

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


Base = declarative_base(cls=BaseModel)
