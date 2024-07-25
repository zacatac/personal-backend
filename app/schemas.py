from typing import Optional
from uuid import UUID
from pydantic import BaseModel, computed_field
import tiktoken

from app.ai import messages_from_context


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
        if self.context is None or len(self.context.get("messages", [])) == 0:
            return 0

        messages_concat = "".join(
            map(
                lambda m: str(m["content"]) if "content" in m else "",
                messages_from_context(self.context),
            )
        )
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(messages_concat))

    class Config:
        orm_mode = True
        json_encoders = {
            UUID: str,
        }
