import asyncio
from typing import AsyncGenerator, Optional, Tuple

import tiktoken
from typing import Any, AsyncGenerator, Dict, List

from sqlalchemy import JSON, Column

from app.types import (
    ChatCompletionAssistantMessageParamID,
    ChatCompletionMessageParamID,
    ChatCompletionUserMessageParamID,
)


def tokens_for_context(context: Optional[dict]) -> int:
    if context is None or len(context.get("messages", [])) == 0:
        return 0

    messages_concat = "".join(
        map(
            lambda m: str(m["content"]) if "content" in m else "",
            messages_from_context(context),
        )
    )
    enc = tiktoken.encoding_for_model("gpt-4o")
    return len(enc.encode(messages_concat))


def messages_from_context(
    context: Dict[str, Any]
) -> List[ChatCompletionMessageParamID]:
    messages_json = context.get("messages", [])
    messages: List[ChatCompletionMessageParamID] = []
    for message in messages_json:
        role = message.get("role")
        content = message.get("content")
        id = message.get("id")
        if role == "user":
            messages.append(
                ChatCompletionUserMessageParamID(role="user", content=content, id=id)
            )
        elif role == "assistant":
            messages.append(
                ChatCompletionAssistantMessageParamID(
                    role="assistant", content=content, id=id
                )
            )
        else:
            raise ValueError("unexpected message role")
    return messages


async def async_tee(
    generator: AsyncGenerator, n: int = 2
) -> Tuple[AsyncGenerator, ...]:
    queues = [asyncio.Queue() for _ in range(n)]

    async def distribute():
        async for item in generator:
            for queue in queues:
                await queue.put(item)
        for queue in queues:
            await queue.put(None)

    asyncio.create_task(distribute())
    return tuple(_queue_to_async_gen(queue) for queue in queues)


async def _queue_to_async_gen(queue: asyncio.Queue) -> AsyncGenerator:
    while True:
        item = await queue.get()
        if item is None:
            break
        yield item
