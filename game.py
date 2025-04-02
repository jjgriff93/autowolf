import logging
import random
from typing import Sequence

from autogen_agentchat.conditions import TimeoutTermination
from autogen_agentchat.messages import ChatMessage
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from autogen_core import ComponentModel
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import AssistantMessage
from fastapi import WebSocket

from models.agent_vote_response import AgentVoteResponse
from roles._role import Role
from roles.seer import Seer
from terminations.text_mention_from_all_termination import TextMentionFromAllTermination
from utils import count_votes

logger = logging.getLogger(__name__)


class WerewolfGame:

    def __init__(self, model_config: ComponentModel, roles: list[Role], ws: WebSocket):
        self.model_config = model_config
        self.round = 1
        self.game_over = False
        self.votes: list[AgentVoteResponse] = []

        random.shuffle(roles)
        self.players = [r(model_config, i + 1) for i, r in enumerate(roles)]

        print("The players and their roles are:")
        for player in self.players:
            print(f"Player {player.id}: {player.role}")

    async def announce_event_to_all(self, message: str):
        """Announce an event to all players."""
        print(message)
        for player in self.players:
            await player.remember_event(message, self.round)

    async def run_phase(
        self,
        task: ChatMessage | str | Sequence[ChatMessage],
        participants: list[Role],
    ):
        """Run a phase of the game with the given task and participants."""
        self.votes.clear()

        async def announce_event_to_participants(message: str):
            """Add messages to only the current participants' event memories"""
            print(message)
            for p in participants:
                await p.remember_event(message, self.round)

        agents = [p.get_agent_for_discussion([p.id for p in participants]) for p in participants]

        if len(agents) > 1:
            team = Swarm(
                agents,
                termination_condition=TimeoutTermination(60)
                | TextMentionFromAllTermination(set([a.name for a in agents]), "READY TO VOTE"),
            )
            # Run the agent(s) discussion and stream the messages to the console.
            task_result = await Console(team.run_stream(task=task))

            # Ask each particpant to individually reflect on the chat history of the round and come up with suspicions/strategy, store to memory
            player_messages = [m for m in task_result.messages if m.type == "ThoughtEvent" or m.type == "TextMessage"]
            discussion_context = UnboundedChatCompletionContext(
                initial_messages=[AssistantMessage(content=m.content, source=m.source) for m in player_messages]
            )
            for p in participants:
                await p.reflect_on_discussion(discussion_context)
        else:
            # If only one agent, run it directly
            task_result = await Console(agents[0].run_stream(task=task))
            discussion_context = UnboundedChatCompletionContext(
                initial_messages=[
                    AssistantMessage(content=m.content, source=m.source)
                    for m in task_result.messages
                    if m.type == "TextMessage"
                ]
            )

        # Hold a vote for elimination
        await announce_event_to_participants("HOST: It's time for the participant(s) to make their vote...")
        for p in participants:
            vote = await p.make_vote(discussion_context)
            self.votes.append(vote)

        # Announce the votes (don't do this as they come in above as it may influence the other players)
        for i, vote in enumerate(self.votes):
            await announce_event_to_participants(
                f"Player {participants[i].id} voted to eliminate Player {vote.player_to_eliminate} because: {vote.reason}"
            )

        # Eliminate the player
        eliminated_player = count_votes([vote.player_to_eliminate for vote in self.votes])
        self.players = [player for player in self.players if player.id != eliminated_player]

        # TODO: differentation between werewolf and villager elimination
        await self.announce_event_to_all(f"HOST: Player {eliminated_player} has been eliminated.")

        # Determine if the game is over
        werewolves = [p for p in self.players if p.role == "werewolf"]

        if len(werewolves) == 0:
            print("No werewolves remain. The villagers have won!")
            self.game_over = True
        elif len(self.players) == 2:
            print("Only 2 players remain, and there is still a werewolf. The werewolf team has won!")
            self.game_over = True
        elif len(werewolves) == len(self.players):
            print(f"No villagers remain. The werewolf team has won!")
            self.game_over = True

        # TODO: save the game state (agent memory, team, round number, current players etc.) to a file

    async def run(self):
        """Run the game until end condition."""
        await self.announce_event_to_all(
            f"HOST: Welcome, villagers... and werewolves! I've dealt out the following roles randomly: {', '.join([p.role for p in self.players])}. Now, let's begin!"
        )
        while not self.game_over:
            # Run day phase
            print("=== DAY PHASE ===")
            await self.run_phase(
                f"HOST: It's Round {self.round}. The day phase has begun. Player {', Player '.join([str(p.id) for p in self.players])}... start your discussions!",
                self.players,
            )

            if self.game_over:
                break

            # Run night phase
            # TODO: split methods into a run_discussion, run_vote
            print("=== NIGHT PHASE ===")
            print("*** Werewolves, wake up... ***")
            werewolves = [p for p in self.players if p.role == "werewolf"]
            task = f"HOST: The night phase has now begun. The villagers are asleep. Werewolves, wake up. You must now decide which villager to kill! The villagers remaining are Player {', Player '.join([str(v.id) for v in self.players if v.role != "werewolf"])}."
            if len(werewolves) > 1:
                task += f" The werewolves remaining are Player {', Player '.join([str(w.id) for w in werewolves])}). You may now discuss your strategy with each other."
            else:
                task += f" You are the only remaining werewolf. You may now reflect on your strategy and consider which players might be a threat to you."
            await self.run_phase(task, werewolves)

            # TODO: if we add more special actions, implement this generically so we can simply iterate
            seer = next((p for p in self.players if isinstance(p, Seer)), None)
            if seer:
                print("*** Seer, wake up... ***")
                await seer.see_another_player(self.players)

            self.round += 1
