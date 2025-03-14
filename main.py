import asyncio
import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from game import WerewolfGame

load_dotenv()

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

model_config = {
    "azure_deployment": os.getenv("MODEL_DEPLOYMENT"),
    "model": os.getenv("MODEL_NAME"),
    "api_version": "2024-10-21",
    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "azure_ad_token_provider": token_provider,
}


async def main() -> None:
    # Pick the roles in play (i.e. the cards to be dealt out)
    roles = [
        "villager",
        "villager",
        "villager",
        "werewolf",
        "seer",
    ]  # TODO: make this user input

    # Create a new game
    game = WerewolfGame(model_config, roles)

    # Run the game
    await game.run()

    # TODO: add seer functionality (perhaps do as separate class of agent with base type, set a Team parameter with either werewolf or villager)
    # TODO: do the same with the werewolf role with more tailored instructions
    # TODO: add user proxy as a player
    # TODO: add randomised personalities
    # TODO: GUI


if __name__ == "__main__":
    asyncio.run(main())
