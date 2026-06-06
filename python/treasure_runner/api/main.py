"""FastAPI server for the Treasure Runner web client."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import (
    ActionResponse,
    CreateGameRequest,
    CreateGameResponse,
    GameStateResponse,
    MoveRequest,
)
from .sessions import SessionStore

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = os.getenv(
    "TREASURE_RUNNER_CONFIG",
    str(REPO_ROOT / "assets" / "starter.ini"),
)
WEB_DIST = REPO_ROOT / "web" / "dist"

app = FastAPI(title="Treasure Runner API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store: SessionStore | None = None
_config_error: str | None = None


def _init_store() -> SessionStore:
    global store, _config_error
    if store is not None:
        return store
    if not Path(DEFAULT_CONFIG).exists():
        _config_error = (
            f"World config not found: {DEFAULT_CONFIG}. "
            "Copy your course assets/starter.ini into the repo, or set TREASURE_RUNNER_CONFIG."
        )
        raise RuntimeError(_config_error)
    store = SessionStore(DEFAULT_CONFIG)
    _config_error = None
    return store


@app.on_event("startup")
def startup() -> None:
    if Path(DEFAULT_CONFIG).exists():
        _init_store()


@app.on_event("shutdown")
def shutdown() -> None:
    if store is None:
        return
    for session_id in list(store._sessions):
        store.destroy(session_id)


def _require_store() -> SessionStore:
    try:
        return _init_store()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok" if _config_error is None else "missing_config",
        "config": DEFAULT_CONFIG,
        "config_exists": Path(DEFAULT_CONFIG).exists(),
        "detail": _config_error,
    }


@app.post("/api/games", response_model=CreateGameResponse)
def create_game(body: CreateGameRequest) -> CreateGameResponse:
    session_store = _require_store()
    try:
        session = session_store.create(body.player_name.strip() or "Player")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    state = GameStateResponse(**session_store.state_dict(session))
    return CreateGameResponse(session_id=session.session_id, state=state)


@app.get("/api/games/{session_id}", response_model=GameStateResponse)
def get_game(session_id: str) -> GameStateResponse:
    session_store = _require_store()
    try:
        session = session_store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc
    return GameStateResponse(**session_store.state_dict(session))


@app.post("/api/games/{session_id}/move", response_model=ActionResponse)
def move_player(session_id: str, body: MoveRequest) -> ActionResponse:
    session_store = _require_store()
    try:
        session = session_store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc

    if session.meta.victory:
        return ActionResponse(state=GameStateResponse(**session_store.state_dict(session)))

    try:
        session_store.move(session, body.direction)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ActionResponse(state=GameStateResponse(**session_store.state_dict(session)))


@app.post("/api/games/{session_id}/portal", response_model=ActionResponse)
def use_portal(session_id: str) -> ActionResponse:
    session_store = _require_store()
    try:
        session = session_store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc

    if not session.meta.victory:
        session_store.portal(session)

    return ActionResponse(state=GameStateResponse(**session_store.state_dict(session)))


@app.post("/api/games/{session_id}/reset", response_model=ActionResponse)
def reset_game(session_id: str) -> ActionResponse:
    session_store = _require_store()
    try:
        session = session_store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Game not found") from exc

    session_store.reset(session)
    return ActionResponse(state=GameStateResponse(**session_store.state_dict(session)))


@app.delete("/api/games/{session_id}")
def delete_game(session_id: str) -> dict:
    session_store = _require_store()
    session_store.destroy(session_id)
    return {"deleted": session_id}


if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        index = WEB_DIST / "index.html"
        if not index.exists():
            raise HTTPException(status_code=404, detail="Frontend not built")
        return FileResponse(index)
