from typing import Any, Dict
import uuid
from sqlalchemy import JSON, UUID, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

    bots = relationship("Bot", back_populates="creator")


class Bot(Base):
    __tablename__ = "bots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    context: Mapped[Dict[str, Any]] = mapped_column(JSON)
    creator_id = Column(UUID, ForeignKey("users.id"))

    creator = relationship("User", back_populates="bots")
