from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Anime(Base):
    __tablename__ = "animes"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    episode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    baidu_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    baidu_password: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quark_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    update_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'anime'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    subscriptions: Mapped[list["UserAnimeSubscription"]] = relationship(
        back_populates="anime", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["AnimeReminder"]] = relationship(
        back_populates="anime", cascade="all, delete-orphan"
    )


class UserAnimeSubscription(Base):
    __tablename__ = "user_anime_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    anime_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("animes.id", ondelete="CASCADE"), nullable=False
    )
    subscribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    anime: Mapped["Anime"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        UniqueConstraint("user_id", "anime_id", name="uq_user_anime"),
        Index("idx_user_anime_subs_user", "user_id"),
    )


class AnimeReminder(Base):
    __tablename__ = "anime_reminders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    anime_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("animes.id", ondelete="CASCADE"), nullable=False
    )
    is_reminded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_episode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    anime: Mapped["Anime"] = relationship(back_populates="reminders")

    __table_args__ = (
        UniqueConstraint("user_id", "anime_id", name="uq_user_anime_reminder"),
        Index("idx_anime_reminders_user", "user_id"),
    )
