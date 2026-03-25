import ctypes
from ..bindings import lib, Status, Direction, GameEngine as GameEnginePtr
from .player import Player
from .exceptions import status_to_exception

class GameEngine:
    """Python wrapper for C GameEngine."""

    def __init__(self, config_path: str):
        """Create game engine from config file."""
        self._eng = GameEnginePtr()
        status = lib.game_engine_create(
            config_path.encode('utf-8'),
            ctypes.byref(self._eng)
        )

        if status != Status.OK:
            raise status_to_exception(status, f"Failed to create game engine: {config_path}")

        # Get player
        player_ptr = lib.game_engine_get_player(self._eng)
        if not player_ptr:
            raise RuntimeError("Failed to get player from game engine")

        self._player = Player(player_ptr)
        self._destroyed = False

    @property
    def player(self) -> Player:
        """Get player object."""
        return self._player

    def destroy(self) -> None:
        """Destroy game engine (safe to call multiple times)."""
        if not self._destroyed:
            lib.game_engine_destroy(self._eng)
            self._destroyed = True

    def move_player(self, direction: Direction) -> None:
        """Move player in given direction."""
        status = lib.game_engine_move_player(self._eng, direction)
        if status != Status.OK:
            raise status_to_exception(status, f"Failed to move player {direction}")

    def render_current_room(self) -> str:
        """Render current room as string."""
        c_str = ctypes.c_char_p()
        status = lib.game_engine_render_current_room(self._eng, ctypes.byref(c_str))

        if status != Status.OK:
            raise status_to_exception(status, "Failed to render room")

        # Decode and free
        result = c_str.value.decode('utf-8')
        lib.game_engine_free_string(c_str)
        return result

    def get_room_count(self) -> int:
        """Get total number of rooms."""
        count = ctypes.c_int()
        status = lib.game_engine_get_room_count(self._eng, ctypes.byref(count))

        if status != Status.OK:
            raise status_to_exception(status, "Failed to get room count")

        return count.value

    def get_room_dimensions(self) -> tuple[int, int]:
        """Get current room dimensions as (width, height)."""
        width = ctypes.c_int()
        height = ctypes.c_int()
        status = lib.game_engine_get_room_dimensions(
            self._eng,
            ctypes.byref(width),
            ctypes.byref(height)
        )

        if status != Status.OK:
            raise status_to_exception(status, "Failed to get room dimensions")

        return (width.value, height.value)

    def get_room_ids(self) -> list[int]:
        """Get list of all room IDs."""
        ids_ptr = ctypes.POINTER(ctypes.c_int)()
        count = ctypes.c_int()

        status = lib.game_engine_get_room_ids(
            self._eng,
            ctypes.byref(ids_ptr),
            ctypes.byref(count)
        )

        if status != Status.OK:
            raise status_to_exception(status, "Failed to get room IDs")

        # Copy to Python list
        result = [ids_ptr[i] for i in range(count.value)]

        # Free C array
        lib.game_engine_free_string(ids_ptr)

        return result

    def reset(self) -> None:
        """Reset game to initial state."""
        status = lib.game_engine_reset(self._eng)
        if status != Status.OK:
            raise status_to_exception(status, "Failed to reset game")

    def __del__(self):
        """Destructor - ensure cleanup."""
        self.destroy()
    
    def get_total_treasure_count(self) -> int:
        """Get total number of treasures across all rooms."""
        count = ctypes.c_int()
        status = lib.game_engine_get_total_treasure_count(
            self._eng, ctypes.byref(count)
        )
        if status != Status.OK:
            raise status_to_exception(status, "Failed to get total treasure count")
        return count.value

    def is_victory(self) -> bool:
        """Return True if every treasure in the world has been collected."""
        result = ctypes.c_int()
        status = lib.game_engine_is_victory(self._eng, ctypes.byref(result))
        if status != Status.OK:
            raise status_to_exception(status, "Failed to check victory")
        return result.value == 1
