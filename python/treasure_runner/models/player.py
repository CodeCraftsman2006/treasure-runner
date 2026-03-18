import ctypes
from ..bindings import lib, Status
from .exceptions import status_to_exception


class Player:
    """Python wrapper for C Player."""

    def __init__(self, ptr):
        """Initialize with C player pointer."""
        self._ptr = ptr

    def get_room(self) -> int:
        """Get current room ID."""
        return lib.player_get_room(self._ptr)

    def get_position(self) -> tuple[int, int]:
        """Get player position as (x, y)."""
        x = ctypes.c_int()
        y = ctypes.c_int()
        status = lib.player_get_position(self._ptr, ctypes.byref(x), ctypes.byref(y))
        if status != Status.OK:
            raise status_to_exception(status, "Failed to get player position")
        return (x.value, y.value)

    def get_collected_count(self) -> int:
        """Get number of collected treasures."""
        return lib.player_get_collected_count(self._ptr)

    def has_collected_treasure(self, treasure_id: int) -> bool:
        """Check if treasure has been collected."""
        return lib.player_has_collected_treasure(self._ptr, treasure_id)

    def get_collected_treasures(self) -> list[dict]:
        """Get list of collected treasures as dicts."""
        count = ctypes.c_int()
        treasures_ptr = lib.player_get_collected_treasures(self._ptr, ctypes.byref(count))

        if not treasures_ptr:
            return []

        result = []
        for i in range(count.value):
            treasure = treasures_ptr[i].contents
            result.append({
                'id': treasure.id,
                'name': treasure.name.decode('utf-8') if treasure.name else None,
                'starting_room_id': treasure.starting_room_id,
                'initial_x': treasure.initial_x,
                'initial_y': treasure.initial_y,
                'x': treasure.x,
                'y': treasure.y,
                'collected': treasure.collected,
            })

        return result
