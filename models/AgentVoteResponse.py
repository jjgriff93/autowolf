from pydantic import BaseModel


class AgentVoteResponse(BaseModel):
    reason: str
    player_to_eliminate: int
