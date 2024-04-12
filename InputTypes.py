from pydantic import BaseModel, Field

class NewPlayer(BaseModel):
    lobby_name: str = Field(..., min_length=1, max_length=20)
    team_name: str = Field(..., min_length=1, max_length=20)
    player_name: str = Field(..., min_length=1, max_length=20)

class Move(BaseModel):
    move: str = Field(..., pattern=r'^(UP|DOWN|LEFT|RIGHT)$')

class Start(BaseModel):
    start: str = Field(..., pattern=r'^(START)$')
