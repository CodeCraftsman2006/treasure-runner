"""In-memory game sessions backed by the C GameEngine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..bindings import Direction
from ..models.exceptions import GameEngineError, ImpassableError
from ..models.game_engine import GameEngine
from .state import SessionMeta, build_state, count_world_treasures

DIRECTION_MAP = {
    "north": Direction.NORTH,
    "south": Direction.SOUTH,
    "east": Direction.EAST,
    "west": Direction.WEST,
    "n": Direction.NORTH,
    "s": Direction.SOUTH,
    "e": Direction.EAST,
    "w": Direction.WEST,
}


@dataclass
class GameSession:
    session_id: str
    engine: GameEngine
    meta: SessionMeta


class SessionStore:
    def __init__(self, config_path: str) -> None:
        self._config_path = config_path
        self._sessions: dict[str, GameSession] = {}

    def create(self, player_name: str) -> GameSession:
        engine = GameEngine(self._config_path)
        total = count_world_treasures(engine)
        session_id = str(uuid.uuid4())
        meta = SessionMeta(player_name=player_name, total_treasures=total)
        session = GameSession(session_id=session_id, engine=engine, meta=meta)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> GameSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def destroy(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            session.engine.destroy()

    def state_dict(self, session: GameSession) -> dict:
        return build_state(session.engine, session.session_id, session.meta)

    def move(self, session: GameSession, direction: str) -> None:
        key = direction.strip().lower()
        if key not in DIRECTION_MAP:
            raise ValueError(f"Invalid direction: {direction}")

        before = session.engine.player.get_collected_count()
        try:
            session.engine.move_player(DIRECTION_MAP[key])
            session.meta.steps += 1
            session.meta.message = ""
            after = session.engine.player.get_collected_count()
            if after > before:
                delta = after - before
                noun = "treasure" if delta == 1 else "treasures"
                session.meta.message = (
                    f"You picked up {delta} {noun}! ({after}/{session.meta.total_treasures})"
                )
                if after >= session.meta.total_treasures:
                    session.meta.victory = True
                    session.meta.message = "All treasure collected! You win!"
        except ImpassableError:
            session.meta.message = "You can't go that way."
        except GameEngineError as exc:
            session.meta.message = str(exc)

    def portal(self, session: GameSession) -> None:
        before_room = session.engine.player.get_room()
        for direction in (
            Direction.NORTH,
            Direction.SOUTH,
            Direction.EAST,
            Direction.WEST,
        ):
            try:
                session.engine.game_engine_try_portal()
                session.meta.steps += 1
                after_room = session.engine.player.get_room()
                if after_room != before_room:
                    session.meta.message = (
                        f"Entered room {after_room + 1} through a portal!"
                    )
                    return
            except (ImpassableError, GameEngineError):
                continue
        session.meta.message = "No portal reachable from here."

    def reset(self, session: GameSession) -> None:
        session.engine.reset()
        session.meta.steps = 0
        session.meta.message = "Game reset to beginning."
        session.meta.victory = False
        session.meta.visited_rooms.clear()
