from typing import Sequence

from autogen_agentchat.base import TerminatedException, TerminationCondition
from autogen_agentchat.messages import AgentEvent, ChatMessage, StopMessage
from autogen_core import Component
from pydantic import BaseModel
from typing_extensions import Self


class TextMentionFromAllTerminationConfig(BaseModel):
    """Configuration for the termination condition to allow for serialization
    and deserialization of the component.
    """

    sources: set[str]
    text: str


class TextMentionFromAllTermination(TerminationCondition, Component[TextMentionFromAllTerminationConfig]):
    """Terminate the conversation if every specified source says the specified text."""

    component_config_schema = TextMentionFromAllTerminationConfig
    """The schema for the component configuration."""

    def __init__(self, sources: set[str], text: str = "**DONE**") -> None:
        self._terminated = False
        self._sources_requesting_termination = set()
        self._sources = sources
        self._termination_text = text

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages: Sequence[AgentEvent | ChatMessage]) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")
        for message in messages:
            if isinstance(message.content, str) and self._termination_text in message.content:
                if message.source in self._sources:
                    self._sources_requesting_termination.add(message.source)
                    if self._sources_requesting_termination == self._sources:
                        self._terminated = True
                        return StopMessage(
                            content=f"Termination condition reached: {self._termination_text} from all sources {self._sources}",
                            source="TextMentionFromAllTermination",
                        )

        return None

    async def reset(self) -> None:
        self._terminated = False

    def _to_config(self) -> TextMentionFromAllTerminationConfig:
        return TextMentionFromAllTerminationConfig(
            text=self._text,
        )

    @classmethod
    def _from_config(cls, config: TextMentionFromAllTerminationConfig) -> Self:
        return cls(
            _text=config.text,
        )
