from autogen_agentchat.agents import AssistantAgent
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from models.seer_choice_response import SeerChoiceResponse
from roles._role import Role
from ui.message_handler import MessageHandler


class Seer(Role):
    """Seer player class."""

    def __init__(self, model_config: dict[str, str], message_handler: MessageHandler, id: int):
        super().__init__(model_config, message_handler, id)
        self.role = "seer"
        self.system_prompt += """
        You've checked your card and found out that you have the role of: seer.

        Tips:
        - Check another player's role each night based on your suspicions
        - Carefully consider the right time to reveal your role and knowledge - it might help but will make you a target for the werewolves
        """

    async def see_another_player(self, players: list[Role]):
        """Choose and see another player's role"""
        model_client = AzureOpenAIChatCompletionClient(response_format=SeerChoiceResponse, **self.model_config)
        agent = AssistantAgent(
            name=f"player_{self.id}",
            model_client=model_client,
            system_message=self.system_prompt,
            memory=[self.events, self.thoughts],
        )
        result = await self.message_handler.send_message_stream(
            agent.run_stream(
                task="HOST: Seer, wake up. Choose a player you'd like to see the role of and provide a brief reason why."
            )
        )
        choice = SeerChoiceResponse.model_validate_json(result.messages[-1].content)
        chosen_player = next(p for p in players if p.id == choice.player_to_see)
        content = MemoryContent(
            content=f"HOST: You chose to see Player {chosen_player.id}'s role because {choice.reason}. They are a {chosen_player.role}.",
            mime_type=MemoryMimeType.TEXT,
        )
        await self.events.add(content)
