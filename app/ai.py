from dataclasses import asdict
import logging

from typing import Any, AsyncGenerator, Dict, Generator, List

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from app.types import (
    ChatCompletionAssistantMessageParamID,
    ChatCompletionMessageParamID,
    ChatCompletionUserMessageParamID,
)


client = AsyncOpenAI()

model = "gpt-4o-mini"

logger = logging.getLogger(__name__)


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


def transform_to_openai_type(
    messages: List[ChatCompletionMessageParamID],
) -> List[ChatCompletionMessageParam]:
    transformed_messages: List[ChatCompletionMessageParam] = []
    for message in messages:
        role = message["role"]
        content = str(message.get("content", "") or "")
        if role == "user":
            transformed_messages.append(
                ChatCompletionUserMessageParam(
                    role="user",
                    content=content,
                )
            )
        elif role == "assistant":
            transformed_messages.append(
                ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=content,
                )
            )
        else:
            raise ValueError("unexpected message type")
    return transformed_messages


async def generate_chat(
    messages: List[ChatCompletionMessageParamID],
) -> AsyncGenerator[str, None]:
    logger.info("generating chat")

    messages_openai = transform_to_openai_type(messages=messages)
    stream = await client.chat.completions.create(
        model=model,
        messages=messages_openai,
        stream=True,
        stream_options={"include_usage": True},
    )

    logger.info("processing stream")
    async for chunk in stream:
        if chunk.usage:
            print(chunk.usage)
        if (
            chunk.choices is not None
            and len(chunk.choices) > 0
            and chunk.choices[0].delta.content is not None
        ):

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
