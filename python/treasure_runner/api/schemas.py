from pydantic import BaseModel, Field


class CreateGameRequest(BaseModel):
    player_name: str = Field(default="Player", min_length=1, max_length=32)


class MoveRequest(BaseModel):
    direction: str = Field(description="north, south, east, or west")


class GameStateResponse(BaseModel):
    session_id: str
    player_name: str
    room_id: int
    room_count: int
    width: int
    height: int
    tiles: list[list[str]]
    player_x: int
    player_y: int
    treasures_collected: int
    total_treasures: int
    steps: int
    message: str
    victory: bool
    visited_rooms: list[int]
    room_ids: list[int]


class CreateGameResponse(BaseModel):
    session_id: str
    state: GameStateResponse


class ActionResponse(BaseModel):
    state: GameStateResponse
