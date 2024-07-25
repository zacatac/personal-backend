from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


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

    class Config:
        orm_mode = True
