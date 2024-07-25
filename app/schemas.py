from typing import Optional
from uuid import UUID
from pydantic import BaseModel, computed_field
import tiktoken

from app.lib import messages_from_context, tokens_for_context


class UserBase(BaseModel):
    clerk_id: str


class UserCreate(UserBase):
    is_active: Optional[bool] = True


class User(UserBase):
    id: UUID
    is_active: bool

    class Config:
        orm_mode = True


class BotBase(BaseModel):
    name: str
    context: Optional[dict] = None


class BotCreate(BotBase):
    creator_id: UUID


class Bot(BotBase):
    id: UUID
    creator_id: UUID
    creator: User

    @computed_field
    @property
    def tokens(self) -> int:
        return tokens_for_context(self.context)

    class Config:
        orm_mode = True
        json_encoders = {
            UUID: str,
        }
