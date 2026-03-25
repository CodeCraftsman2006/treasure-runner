"""
 Low-level ctypes bindings

This module provides direct ctypes access to the C library functions.
It handles:
  - Loading the shared library
  - Defining C enums and structures
  - Wrapping C function signatures
  - Managing error codes from the C layer

This is a thin layer - no error handling or convenience wrappers.
All error handling is done in the models layer.
"""

import ctypes
import os
from enum import IntEnum
from pathlib import Path


# ============================================================
# Enums matching C definitions
# ============================================================

class Direction(IntEnum):
    """Movement directions (matches DIR_* in types.h)."""
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3


class Status(IntEnum):
    """Status codes for room and player operations."""
    OK = 0
    INVALID_ARGUMENT = 1
    NULL_POINTER = 2
    NO_MEMORY = 3
    BOUNDS_EXCEEDED = 4
    INTERNAL_ERROR = 5
    ROOM_IMPASSABLE = 6
    ROOM_NO_PORTAL = 7
    ROOM_NOT_FOUND = 8
    GE_NO_SUCH_ROOM = 9
    WL_ERR_CONFIG = 10
    WL_ERR_DATAGEN = 11

# Backwards compatibility for existing imports
GameEngineStatus = Status


# ============================================================
# C Structures - Opaque types only
# ============================================================

# Treasure is used by player_get_collected_treasures
class Treasure(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("name", ctypes.c_char_p),
        ("starting_room_id", ctypes.c_int),
        ("initial_x", ctypes.c_int),
        ("initial_y", ctypes.c_int),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("collected", ctypes.c_bool),
    ]


# ============================================================
# Library Loading
# ============================================================

def _find_library():
    """Locate libbackend.so under the project dist directory."""
    # Optional override via env
    env_path = os.getenv("TREASURE_RUNNER_DIST")
    candidates = []

    if env_path:
        candidates.append(Path(env_path) / "libbackend.so")
        candidates.append(Path(env_path) / "libpuzzlegen.so")

    # Project-relative: ../../dist relative to this file
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent.parent
    candidates.append(repo_root / "dist" / "libbackend.so")
    candidates.append(repo_root / "dist" / "libpuzzlegen.so")
    #candidates.append(repo_root / "c" / "lib" / "libbackend.so")
    #candidates.append(repo_root / "c" / "lib" / "libpuzzlegen.so")

    found = {}
    for path in candidates:
        if path.exists():
            found[path.name] = path

    if "libbackend.so" in found:
        # Ensure puzzlegen is loaded first if present to satisfy dependencies.
        puzzlegen = found.get("libpuzzlegen.so")
        if puzzlegen:
            ctypes.CDLL(str(puzzlegen))
        return str(found["libbackend.so"])

    tried = "\n".join(str(p) for p in candidates)
    raise RuntimeError(f"libbackend.so not found. Paths tried:\n{tried}")


# Load the library
_LIB_PATH = _find_library()
lib = ctypes.CDLL(_LIB_PATH)


# ============================================================
# C Function Signatures
# ============================================================

# Opaque pointer type for GameEngine
GameEngine = ctypes.c_void_p




# ============================================================
# C Function Signatures - Player
# ============================================================

# Opaque pointer type for Player
Player = ctypes.c_void_p



# ============================================================
# C Function Signatures - Room
# ============================================================

# Room is opaque - no direct room accessors exposed to Python
Room = ctypes.c_void_p


# ============================================================
# Memory Management
# ============================================================
# Game engine lifecycle


lib.player_get_collected_count.argtypes = [Player]
lib.player_get_collected_count.restype = ctypes.c_int

lib.player_has_collected_treasure.argtypes = [Player, ctypes.c_int]
lib.player_has_collected_treasure.restype = ctypes.c_bool

lib.player_get_room.argtypes = [Player]
lib.player_get_room.restype = ctypes.c_int

lib.player_get_position.argtypes = [Player, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
lib.player_get_position.restype = ctypes.c_int

lib.player_get_collected_treasures.argtypes = [Player, ctypes.POINTER(ctypes.c_int)]
lib.player_get_collected_treasures.restype = ctypes.POINTER(ctypes.POINTER(Treasure))

lib.player_reset_to_start.argtypes = [Player, ctypes.c_int, ctypes.c_int, ctypes.c_int]
lib.player_reset_to_start.restype = ctypes.c_int

lib.game_engine_create.argtypes = [ctypes.c_char_p, ctypes.POINTER(GameEngine)]
lib.game_engine_create.restype = ctypes.c_int

lib.game_engine_destroy.argtypes = [GameEngine]
lib.game_engine_destroy.restype = None

lib.game_engine_get_player.argtypes = [GameEngine]
lib.game_engine_get_player.restype = Player

lib.game_engine_move_player.argtypes = [GameEngine, ctypes.c_int]
lib.game_engine_move_player.restype = ctypes.c_int

lib.game_engine_reset.argtypes = [GameEngine]
lib.game_engine_reset.restype = ctypes.c_int

lib.game_engine_render_current_room.argtypes = [GameEngine, ctypes.POINTER(ctypes.c_char_p)]
lib.game_engine_render_current_room.restype = ctypes.c_int

lib.game_engine_get_room_count.argtypes = [GameEngine, ctypes.POINTER(ctypes.c_int)]
lib.game_engine_get_room_count.restype = ctypes.c_int

lib.game_engine_get_room_dimensions.argtypes = [GameEngine, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
lib.game_engine_get_room_dimensions.restype = ctypes.c_int

lib.game_engine_get_room_ids.argtypes = [GameEngine, ctypes.POINTER(ctypes.POINTER(ctypes.c_int)), ctypes.POINTER(ctypes.c_int)]
lib.game_engine_get_room_ids.restype = ctypes.c_int


lib.game_engine_free_string.argtypes = [ctypes.c_void_p]
lib.game_engine_free_string.restype = None

lib.game_engine_get_total_treasure_count.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)
]
lib.game_engine_get_total_treasure_count.restype = ctypes.c_int

lib.game_engine_is_victory.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)
]
lib.game_engine_is_victory.restype = ctypes.c_int