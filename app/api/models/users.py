import uuid
from uuid6 import uuid7
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    func,
    UUID,
    Text,
    Index,
    Boolean,
    VARCHAR,
    DateTime,
    PrimaryKeyConstraint,
)


from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid7())
    first_name: Mapped[str] = mapped_column(VARCHAR)
    last_name: Mapped[str] = mapped_column(VARCHAR)
    email: Mapped[str] = mapped_column(VARCHAR, unique=True)
    hashed_password: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_users_email", email),
        PrimaryKeyConstraint("id", name="users_id_pk"),
    )

class GoogleUser(Base):
    __tablename__ = "google_users"

    user_id: Mapped[str | None] = mapped_column(VARCHAR)
    first_name: Mapped[str] = mapped_column(VARCHAR)
    last_name: Mapped[str] = mapped_column(VARCHAR)
    email: Mapped[str] = mapped_column(VARCHAR, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_google_users_id", user_id),
        PrimaryKeyConstraint("user_id", name="google_users_id_pk"),
    )
