import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)       # internal key
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)             # shown to user
    description: Mapped[str] = mapped_column(Text, nullable=True)
    component_key: Mapped[str] = mapped_column(String(100), nullable=False)            # React component name
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)               # chart/table/card/form
    default_config: Mapped[dict] = mapped_column(JSON, nullable=True)                  # {w, h, x, y}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    widget_permissions: Mapped[list["WidgetPermission"]] = relationship("WidgetPermission", back_populates="widget", cascade="all, delete-orphan")


class WidgetPermission(Base):
    """Which permission is required to see a widget"""
    __tablename__ = "widget_permissions"

    widget_id: Mapped[str] = mapped_column(String, ForeignKey("widgets.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[str] = mapped_column(String, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    widget: Mapped["Widget"] = relationship("Widget", back_populates="widget_permissions")
    permission: Mapped["Permission"] = relationship("Permission")


class UserWidgetPreference(Base):
    """Stores per-user widget visibility preferences"""
    __tablename__ = "user_widget_preferences"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    widget_id: Mapped[str] = mapped_column(String, ForeignKey("widgets.id", ondelete="CASCADE"), primary_key=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[dict] = mapped_column(JSON, nullable=True)   # {x, y, w, h}
