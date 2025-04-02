import copy
from abc import ABC

from autogen_agentchat.agents import AssistantAgent
from autogen_core import ComponentModel
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import ChatCompletionClient
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from models.agent_vote_response import AgentVoteResponse


class Role(ABC):
    """A base role used to implement a player in the Werewolf game."""

    def __init__(
        self,
        model_config: ComponentModel,
        id: int,
    ):
        self.id = id
        self.model_config = model_config

        # Create a memory for recording the player's internal thoughts
        self.thoughts = ListMemory(name="thoughts")  # TODO: change to vector and make persistent
        self.events = ListMemory(name="events")  # TODO: change to vector and make persistent
        self.system_prompt = f"""
      You are Player {id} in a game of Werewolf.

      Objectives:
      - The game is divided into two teams: the werewolves and the villagers
      - The werewolves must kill off the villagers without being caught
      - The villagers (which includes seer) must identify the werewolves and kill them off

      How it works:
      - Each round consists of a day and a night phase
      - During the day players will discuss your suspicions for who is a werewolf
      - Players will individually vote for another player to eliminate with a reason for their vote, which everyone will see
      - The HOST will announce the votes and the player that was eliminated
      - The night phase will then begin and the werewolves will discuss who to kill
      - The werewolves will then vote for a player to eliminate
      - If the seer is in the game, they will select a player and will see their role
      - The HOST will tell you who has been killed and the day phase will begin again
      - The game ends when there is only either villagers or werewolves remaining, or if only 2 players are left, in which case if a werewolf remains, they win

      Rules:
      - Follow the HOST's instructions and do not break character
      - DO NOT output your internal monologue/strategy in the day phase discussions as the other players will see it
      - DO NOT take on the role of the HOST or any other player at any point
      - DO NOT proceed to the next phase until you're told to by the HOST
      - DO NOT vote for yourself
      - In discussions, after you've spoken, either handoff to another specific player to ask a direct question, otherwise handoff randomly to another player
      - Discussions with other players will end either after 60 seconds or until all have uttered **READY TO VOTE**
    """

    def get_agent_for_discussion(self, player_ids: list[int]) -> AssistantAgent:
        """Create agent to discuss with other players"""
        if len(player_ids) > 1:
            handoffs = [f"player_{id}" for id in player_ids if id != self.id]
            client_without_parallel_tools = copy.replace(self.model_config, {"config.parallel_tool_calls": False})
            client = ChatCompletionClient.load_component(client_without_parallel_tools)
        else:
            handoffs = None
            client = AzureOpenAIChatCompletionClient(**self.model_config)

        return AssistantAgent(
            name=f"player_{self.id}",
            model_client=client,
            handoffs=handoffs,
            memory=[self.events, self.thoughts],
            system_message=self.system_prompt,
            model_client_stream=True,
        )

    async def make_vote(self, chat_context: ChatCompletionContext) -> AgentVoteResponse:
        """Tell agent to make a vote"""
        model_client = AzureOpenAIChatCompletionClient(response_format=AgentVoteResponse, **self.model_config)
        agent = AssistantAgent(
            name=f"player_{self.id}",
            model_client=model_client,
            model_context=chat_context,
            system_message=self.system_prompt,
            memory=[self.events, self.thoughts],
            model_client_stream=True,
        )
        result = await agent.run(
            task="HOST: use your memories and thoughts from previous discussions to determine the player you'd like to eliminate with a brief reason why."
        )
        message = AgentVoteResponse.model_validate_json(result.messages[-1].content)
        return message

    async def reflect_on_discussion(self, chat_context: ChatCompletionContext):
        """Reflect on the discussion and store summary to memory"""
        # TODO: can we remove the need to keep creating a new agent for each task?
        agent = AssistantAgent(
            name=f"player_{self.id}",
            model_client=AzureOpenAIChatCompletionClient(**self.model_config),
            model_context=chat_context,
            system_message=self.system_prompt,
            memory=[self.events, self.thoughts],
            tools=[self.add_internal_thought],
            model_client_stream=True,
        )
        await agent.run(
            task="HOST: discussion has ended. Please reflect on the discussion and summarise things that stood out, suspicions of other players or potential strategies and record them to your memory."
        )

    async def remember_event(self, event: str, round: int):
        """Add a game event to the player's memory."""
        content = MemoryContent(
            content=event, mime_type=MemoryMimeType.TEXT, metadata={"type": "event", "round": round}
        )
        await self.events.add(content)

    async def add_internal_thought(self, content: str, round: int):
        """Add an internal thought to the agent's memory."""
        content = MemoryContent(
            content=content, mime_type=MemoryMimeType.TEXT, metadata={"type": "thought", "round": round}
        )
        await self.thoughts.add(content)
