from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import User


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), nullable=False)
    rarity: Mapped[str] = mapped_column(String(10), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_value: Mapped[int] = mapped_column(Integer, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    badge_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    user: Mapped["User"] = relationship("User")
    badge: Mapped["Badge"] = relationship("Badge")

    __table_args__ = (
        Index("idx_user_badges_user_id", "user_id"),
    )