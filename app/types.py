from dataclasses import dataclass
from typing import Union
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionUserMessageParam,
)

from uuid import UUID


@dataclass
class ChatCompletionAssistantMessageParamID(ChatCompletionAssistantMessageParam):
    id: str  # UUID


@dataclass
class ChatCompletionUserMessageParamID(ChatCompletionUserMessageParam):
    id: str  # UUID


ChatCompletionMessageParamID = Union[
    ChatCompletionAssistantMessageParamID,
    ChatCompletionUserMessageParamID,
]
