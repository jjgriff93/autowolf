from pydantic import BaseModel


class SeerChoiceResponse(BaseModel):
    reason: str
    player_to_see: int
