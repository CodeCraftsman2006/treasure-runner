"""Build JSON game state from a live GameEngine session."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..bindings import Direction
from ..models.exceptions import GameEngineError, ImpassableError
from ..models.game_engine import GameEngine


TILE_WALL = "#"
TILE_PLAYER = "@"
TILE_TREASURE = "$"
TILE_PORTAL = {"X", "x"}


def parse_room_grid(render: str) -> list[list[str]]:
    lines = [line.rstrip("\r") for line in render.splitlines() if line.strip()]
    return [list(row) for row in lines]


@dataclass
class SessionMeta:
    player_name: str
    steps: int = 0
    message: str = ""
    victory: bool = False
    total_treasures: int = 0
    visited_rooms: set[int] = field(default_factory=set)


def count_world_treasures(engine: GameEngine) -> int:
    """Walk reachable rooms once to count all treasure tiles."""
    total = 0
    try:
        engine.reset()
        room_ids = engine.get_room_ids()
        visited: set[int] = set()

        def visit_room() -> None:
            nonlocal total
            rid = engine.player.get_room()
            if rid in visited:
                return
            render = engine.render_current_room()
            total += render.count(TILE_TREASURE)
            visited.add(rid)

        def try_move(direction: Direction) -> bool:
            try:
                engine.move_player(direction)
                return True
            except (ImpassableError, GameEngineError):
                return False

        visit_room()
        for _ in range(len(room_ids) * 100):
            if len(visited) == len(room_ids):
                break
            current = engine.player.get_room()
            for direction in (Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST):
                if not try_move(direction):
                    continue
                neighbour = engine.player.get_room()
                if neighbour != current:
                    visit_room()
            for _ in range(10):
                try:
                    before = engine.player.get_room()
                    engine.game_engine_try_portal()
                    after = engine.player.get_room()
                    if after != before:
                        visit_room()
                except (ImpassableError, GameEngineError):
                    break
    finally:
        engine.reset()

    return total


def build_state(engine: GameEngine, session_id: str, meta: SessionMeta) -> dict:
    render = engine.render_current_room()
    tiles = parse_room_grid(render)
    width, height = engine.get_room_dimensions()
    player = engine.player
    room_id = player.get_room()
    meta.visited_rooms.add(room_id)

    collected = player.get_collected_count()
    victory = meta.victory or (
        meta.total_treasures > 0 and collected >= meta.total_treasures
    )
    if victory:
        meta.victory = True
        if not meta.message:
            meta.message = "All treasure collected! You win!"

    return {
        "session_id": session_id,
        "player_name": meta.player_name,
        "room_id": room_id,
        "room_count": engine.get_room_count(),
        "width": width,
        "height": height,
        "tiles": tiles,
        "player_x": player.get_position()[0],
        "player_y": player.get_position()[1],
        "treasures_collected": collected,
        "total_treasures": meta.total_treasures,
        "steps": meta.steps,
        "message": meta.message,
        "victory": meta.victory,
        "visited_rooms": sorted(meta.visited_rooms),
        "room_ids": engine.get_room_ids(),
    }
