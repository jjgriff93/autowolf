import os
import chainlit as cl

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from game import WerewolfGame
from roles.seer import Seer
from roles.villager import Villager
from roles.werewolf import Werewolf
from ui.message_handler import MessageHandler

load_dotenv()

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

model_config = {
    "azure_deployment": os.getenv("MODEL_DEPLOYMENT"),
    "model": os.getenv("MODEL_NAME"),
    "api_version": "2024-10-21",
    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "azure_ad_token_provider": token_provider,
}

message_handler = MessageHandler()


@cl.on_chat_start
async def on_chat_start():
    # Pick the roles in play (i.e. the cards to be dealt out)
    roles = [
        Villager,
        Villager,
        Villager,
        Werewolf,
        Seer,
    ]

    # Create a new game
    game = WerewolfGame(model_config, message_handler, roles)
    await game.run()
