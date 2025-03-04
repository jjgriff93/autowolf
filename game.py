import random
from typing import Sequence

from autogen_agentchat.conditions import ExternalTermination
from autogen_agentchat.messages import ChatMessage
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from autogen_core.models import ChatCompletionClient

from agents.player import WerewolfPlayer
from utils import count_votes


class WerewolfGame:

    def __init__(self, model_client: ChatCompletionClient, roles: list[str]):
        self.model_client = model_client
        self.round = 1
        self.game_over = False
        self.votes: list[int] = []
        self.termination = ExternalTermination()

        def vote(target: int) -> None:
            print(f"Player {target} has been voted for.")
            self.votes.append(target)

            # If all players have voted, terminate the chat
            if len(self.votes) == len(self.players):
                self.termination.set()

        random.shuffle(roles)
        self.players = [WerewolfPlayer(model_client, i + 1, role, roles, vote) for i, role in enumerate(roles)]

        print("The players and their roles are:")
        for player in self.players:
            print(f"Player {player.id}: {player.role}")

    async def run_phase(
        self,
        task: ChatMessage | str | Sequence[ChatMessage],
        participants: list[WerewolfPlayer],
    ):
        self.votes.clear()

        if len(participants) > 1:
            # TODO: how do we carry over group context from previous phases?
            team = Swarm(
                [p.agent for p in participants],
                max_turns=20,  # TODO: change to a time limit with human in the loop
                termination_condition=self.termination,
            )

            # Run the agent and stream the messages to the console.
            await Console(team.run_stream(task=task))

            # Ensure all players have voted
            while len(self.votes) < len(participants):
                print("Not all players have voted. Prompting for a final vote...")
                # TODO: instead of running team again, could we iterate through the players directly and ask them to vote? Will need team context (memory?)
                await Console(
                    team.run_stream(
                        task="HOST: discussion is over! Some of you haven't voted yet - please immediately vote for a player to be eliminated."
                    ),
                )
        else:
            await Console(participants[0].agent.run_stream(task=task))
            while len(self.votes) < 1:
                print("Player didn't vote. Prompting them...")
                await Console(
                    participants[0].agent.run_stream(
                        task="HOST: you didn't vote. Please immediately make your vote for the player to eliminate."
                    ),
                )

        # Eliminate the player
        eliminated_player = count_votes(self.votes)
        self.players = [player for player in self.players if player.id != eliminated_player]
        print(f"Player {eliminated_player} has been eliminated.")  # TODO: how do we add these messages to the context

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
        else:
            print("Werewolves and villagers still remain. The game continues...")

    async def run(self):
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
            print("=== NIGHT PHASE ===")
            await self.run_phase(
                f"HOST: The night phase has now begun. The villagers are asleep. You must now decide which villager to kill! The villagers remaining are {', Player '.join([str(v.id) for v in self.players if v.role != "werewolf"])}.",
                [p for p in self.players if p.role == "werewolf"],
            )

            self.round += 1
