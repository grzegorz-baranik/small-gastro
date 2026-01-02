from sqlalchemy import create_engine, Enum as SQLAlchemyEnum
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings
from enum import Enum

settings = get_settings()

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def EnumColumn(enum_class: type[Enum], **kwargs):
    """
    Create a SQLAlchemy Enum column that uses enum VALUES (not names).

    IMPORTANT: Always use this helper instead of raw SQLAlchemy Enum!

    Problem it solves:
        PostgreSQL enums are created with lowercase values ('expense', 'revenue'),
        but SQLAlchemy's default Enum uses uppercase NAMES ('EXPENSE', 'REVENUE').
        This causes: "invalid input value for enum" errors on all queries.

    Usage:
        from app.core.database import Base, EnumColumn

        class MyModel(Base):
            status = Column(EnumColumn(MyStatusEnum), nullable=False)

    Instead of:
        status = Column(Enum(MyStatusEnum), nullable=False)  # DON'T DO THIS!
    """
    return SQLAlchemyEnum(
        enum_class,
        values_callable=lambda x: [e.value for e in x],
        **kwargs
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
