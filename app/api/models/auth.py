import uuid
from uuid6 import uuid7
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    text,
    func,
    UUID,
    Index,
    VARCHAR,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
)

from app.database.base import Base


class AuthOtp(Base):
    __tablename__ = "otp"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, default=uuid7()
    )
    otp: Mapped[str] = mapped_column(VARCHAR)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", name="otp_user_id_fk", ondelete="CASCADE")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_auth_otp", otp),
        PrimaryKeyConstraint("id", name="auth_otp_id_pk"),
    )

    user = relationship("User", viewonly=True, lazy="selectin")
