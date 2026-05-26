from datetime import date, datetime

from sqlalchemy import DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    openid: Mapped[str] = mapped_column(String(64), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'用户'"))
    avatar: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'👤'"))
    invite_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    continuous_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    activity_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'"))
    last_record_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("idx_users_openid", "openid", unique=True),
        Index("idx_users_invite_count", "invite_count"),
    )