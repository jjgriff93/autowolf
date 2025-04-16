import chainlit as cl

from typing import AsyncGenerator, Optional, TypeVar
from autogen_agentchat.base import Response, TaskResult
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    ThoughtEvent,
    TextMessage,
    ToolCallExecutionEvent
)

from ui.task_handler import TaskHandler

T = TypeVar("T", bound=TaskResult | Response)


class MessageHandler:
    def __init__(self):
        self.task_handler = TaskHandler()
        self.current_message = None
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
            match message:
                case TaskResult():
                    return message
                case ToolCallExecutionEvent():
                    for content in message.content:
                        await self.task_handler.send_task(content.content)
                case ThoughtEvent() | TextMessage():
                    await self.send_message(message.content, message.source)
