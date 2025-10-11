from sqlmodel import SQLModel

NAMING_CONVENTION = {
    "ix": "123ix_%(column_0_label)s",
    "uq": "1234uq_%(table_name)s_%(column_0_name)s",
    "ck": "123ck_%(table_name)s_%(constraint_name)s",
    "fk": "123fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "123pk_%(table_name)s",
}

SQLModel.metadata.naming_convention = NAMING_CONVENTION

__all__ = ["SQLModel"]
