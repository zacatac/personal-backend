from sqlalchemy import JSON, UUID, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True, index=True)
    clerk_id = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

    bots = relationship("Bot", back_populates="creator")


class Bot(Base):
    __tablename__ = "bots"

    id = Column(UUID, primary_key=True)
    name = Column(String, index=True)
    context = Column(JSON)
    creator_id = Column(UUID, ForeignKey("users.id"))

    creator = relationship("User", back_populates="bots")
