from typing import Callable

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff
from autogen_core.memory import ListMemory
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient


class WerewolfPlayer:
    def __init__(
        self,
        model_client: AzureOpenAIChatCompletionClient,
        id: int,
        role: str,
        all_roles: list[str],
        on_vote: Callable[[int], None],
    ):
        self.id = id
        self.on_vote = on_vote
        self.role = role
        self.system_prompt = f"""
      You are Player {id} in a game of Werewolf.

      Objectives:
      - The game is divided into two teams: the werewolves and the villagers.
      - The werewolves must kill off the villagers without being caught.
      - The villagers (which includes seer) must identify the werewolves and kill them off.

      How it works:
      - Each round consists of a day and a night phase.
      - During the day you and the other players will discuss your suspicions for who is a werewolf.
      - Once you've had some discussions and have a suspicion, make your vote by calling the vote function with the player ID of the target.
      - After making your vote, stay quiet and let the other players continue their discussion and make their votes.
      - Once all votes are in the host will tell you the results and who has been eliminated.
      - The night phase will then begin and the werewolves will choose a player to eliminate.
      - The host will tell you who has been killed and the day phase will begin again.
      - The game ends when there is only either villagers or werewolves remaining, or if only 2 players are left, in which case if a werewolf remains, they win.

      Tips:
      - If you're a villager, try to work with others and figure out who the werewolves are, depending on how players are acting and whether what they're saying makes sense.
      - If you're a werewolf, make sure to blend in and not attract suspicion. Pretend you're another role and that you're helping out the villagers.
      
      DO NOT output your internal monologue/strategy as the other players will see it.

      Your host will tell you when each phase starts and ends. Don't proceed to the next phase until you're told to do so.
      In discussions, handoff/transfer to a specific player if you want to ask them a direct question, otherwise handoff randomly.
      Always send a response to the discussion first before transferring.

      The possible roles in play (comma-separated) are: {','.join(all_roles)}.

      You've just checked your card and found out that you have the role of {role}.
    """
        self.agent = AssistantAgent(
            name=f"player_{id}",
            model_client=model_client,
            tools=[self.vote],
            handoffs=[f"player_{i}" for i in range(1, len(all_roles) + 1) if i != id],
            # memory=ListMemory(),
            system_message=self.system_prompt,
            reflect_on_tool_use=True,
            model_client_stream=True,  # Enable streaming tokens from the model client.
        )

    def vote(self, target: int):
        """Vote for a player to be eliminated.
        Args:
            target (int): The player ID of the target to vote for.
        """
        self.on_vote(target)

    # TODO: add to memory method for internal monolgue / suspicion tracking
