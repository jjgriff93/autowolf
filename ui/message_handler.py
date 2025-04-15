import chainlit as cl

from typing import AsyncGenerator, Optional, TypeVar
from autogen_agentchat.base import Response, TaskResult
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    ThoughtEvent,
    TextMessage
)

T = TypeVar("T", bound=TaskResult | Response)


class MessageHandler:
    def __init__(self):
        pass

    async def send_message(self, message: str, author: Optional[str] = None):
        """Send a message to the UI."""
        author = author or "host"
        await cl.Message(
            content=f"[{author}] {message}",
            author=author
        ).send()

    async def send_message_stream(self, stream: AsyncGenerator[BaseAgentEvent | BaseChatMessage | T, None]) -> TaskResult:
        """Stream messages to the UI."""
        async for message in stream:
            if isinstance(message, TaskResult):
                return message

            if isinstance(message, ThoughtEvent) or isinstance(message, TextMessage):
                await self.send_message(message.content, message.source)
