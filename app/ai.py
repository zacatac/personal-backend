import logging

from typing import Any, AsyncGenerator, Dict, Generator, List

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)

client = AsyncOpenAI()

model = "gpt-4o-mini"

logger = logging.getLogger(__name__)


def messages_from_context(context: Dict[str, Any]) -> List[ChatCompletionMessageParam]:
    messages_json = context.get("messages", [])
    messages: List[ChatCompletionMessageParam] = []
    for message in messages_json:
        role = message.get("role")
        content = message.get("content")
        if role == "user":
            messages.append(
                ChatCompletionUserMessageParam(role="user", content=content)
            )
        elif role == "assistant":
            messages.append(
                ChatCompletionAssistantMessageParam(role="assistant", content=content)
            )
        else:
            raise ValueError("unexpected message role")
    return messages


async def generate_chat(
    messages: List[ChatCompletionMessageParam],
) -> AsyncGenerator[str, None]:
    logger.info("generating chat")

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )

    logger.info("processing stream")
    async for chunk in stream:
        if chunk.usage:
            print(chunk.usage)
        if chunk.choices is not None and chunk.choices[0].delta.content is not None:

            content = chunk.choices[0].delta.content
            yield content


def response_for_stream(stream) -> str:
    response: str = ""

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            response += content
    return response


if __name__ == "__main__":
    messages: List[ChatCompletionMessageParam] = [
        ChatCompletionUserMessageParam(
            role="user", content="Say this is a test 2 times."
        )
    ]

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    response = response_for_stream(stream=stream)

    print(f"full response: {response}")

    print("making a followup request")

    messages.append(
        ChatCompletionAssistantMessageParam(role="assistant", content=response)
    )
    messages.append(ChatCompletionUserMessageParam(role="user", content="Thanks!"))

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    response = response_for_stream(stream=stream)

    print(f"followup response: {response}")
