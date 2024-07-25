from typing import Any, AsyncGenerator, List
from uuid import UUID
from openai.types.chat import ChatCompletionMessageParam
from sqlalchemy import Column
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app import models


def get_or_create_user(db: Session, clerk_id: str):
    user = db.query(models.User).filter(models.User.clerk_id == clerk_id).first()
    if user is None:
        db_user = models.User(clerk_id=clerk_id)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        user = db_user
    return user


def get_or_create_bot(db: Session, user_id: Column[UUID]):
    bot = db.query(models.Bot).filter(models.Bot.creator_id == user_id).first()
    if bot is None:
        db_bot = models.Bot(creator_id=user_id)
        db.add(db_bot)
        db.commit()
        db.refresh(db_bot)
        bot = db_bot
    return bot


async def persist_next_message(
    db: Session,
    bot: models.Bot,
    accumulator: AsyncGenerator[Any, None],
    messages: List[ChatCompletionMessageParam],
    input_message: str,
):
    latest_message = ""
    async for item in accumulator:
        latest_message += item
    messages.extend(
        [
            {
                "role": "user",
                "content": input_message,
            },
            {
                "role": "assistant",
                "content": latest_message,
            },
        ]
    )
    if bot.context is None:
        bot.context = {"messages": []}
    bot.context["messages"] = messages
    flag_modified(bot, "context")
    db.add(bot)
    db.commit()
