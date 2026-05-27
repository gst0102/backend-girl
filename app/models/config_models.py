from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ConfigUnlock(Base):
    __tablename__ = "config_unlock"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_key: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    feature_name: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("idx_config_unlock_threshold", "threshold"),
    )


class ConfigPushTemplate(Base):
    __tablename__ = "config_push_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    wechat_template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wechat_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_config_push_templates_template_id", "template_id", unique=True),
    )


class AdConfig(Base):
    __tablename__ = "ad_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ad_type: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unit_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    test_unit_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    position: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ab_test_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ab_test_ratio: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class MarqueeConfig(Base):
    __tablename__ = "marquee_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=True)
    link_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    screenshots: Mapped[str] = mapped_column(Text, nullable=True)  # JSON 格式的截图列表
    contact: Mapped[str] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'pending'"))
    admin_reply: Mapped[str] = mapped_column(Text, nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class SystemConfig(Base):
    """系统配置表 - 全局系统级配置 (key-value)"""
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    config_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class MineSection(Base):
    """Mine页板块配置表 - '我的'页面各板块标题和开关"""
    __tablename__ = "mine_sections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    section_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_mine_sections_sort", "sort_order"),
    )
