from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config.settings import settings

Base = declarative_base()

# Sync engine for migrations
sync_engine = create_engine(settings.database_url_sync, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
