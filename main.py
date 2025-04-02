import json
import logging
import os
from typing import Any, Awaitable, Callable, Optional

import aiofiles
import yaml
from autogen_core import CancellationToken, ComponentModel
from autogen_core.models import ChatCompletionClient
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from game import WerewolfGame
from roles.seer import Seer
from roles.villager import Villager
from roles.werewolf import Werewolf

logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="."), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def root():
    """Serve webpage"""
    return FileResponse("index.html")


@app.websocket("/ws/game/new")
async def new_game(websocket: WebSocket):
    await websocket.accept()

    # Pick the roles in play (i.e. the cards to be dealt out)
    roles = [
        Villager,
        Villager,
        Villager,
        Werewolf,
        Seer,
    ]  # TODO: make this user input and validate number of allowed roles depending on number of players

    # Get model component config (using yaml template)
    async with aiofiles.open("model_config.yaml", "r") as file:
        model_base_config = yaml.safe_load(await file.read())

    # Create a new game
    game = WerewolfGame(model_base_config, roles, websocket)

    # Run the game
    try:
        logger.info("Starting game...")
        await game.run()
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "content": f"Unexpected error: {str(e)}", "source": "system"})
        except:
            pass

    # TODO: add user proxy as a player
    # TODO: add randomised personalities
    # TODO: GUI


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
