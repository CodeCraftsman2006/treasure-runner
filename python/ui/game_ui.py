"""
GameUI: Curses-based view for Treasure Run.

Handles all rendering, input, and screen layout.
The controller (GameEngine) is queried for state; this class
never touches ctypes or C pointers directly.
"""

import curses
import json
from datetime import datetime, timezone
from typing import Optional

from ..models.exceptions import ImpassableError, GameEngineError
from ..bindings import Direction


MIN_ROWS = 24
MIN_COLS = 80

KEY_MAP = {
    curses.KEY_UP: Direction.NORTH,
    ord("w"): Direction.NORTH,
    ord("W"): Direction.NORTH,
    curses.KEY_DOWN: Direction.SOUTH,
    ord("s"): Direction.SOUTH,
    ord("S"): Direction.SOUTH,
    curses.KEY_RIGHT: Direction.EAST,
    ord("d"): Direction.EAST,
    ord("D"): Direction.EAST,
    curses.KEY_LEFT: Direction.WEST,
    ord("a"): Direction.WEST,
    ord("A"): Direction.WEST,
}

CONTROLS = "Arrows/WASD: move  >: portal  r: reset  q: quit"


class TerminalTooSmallError(Exception):
    """Raised when the terminal is too small to display the game."""


class GameUI:
    """Curses view for Treasure Run."""

    def __init__(self, engine, profile: dict, profile_path: str):
        self._engine = engine
        self._profile = profile
        self._profile_path = profile_path
        self._message = "Welcome! Use arrows or WASD to move."
        self._steps = 0
        self._stdscr: Optional["curses._CursesWindow"] = None
        self._victory = False

    def run(self) -> None:
        """Launch the curses wrapper and start the game."""
        curses.wrapper(self._main)

    def _main(self, stdscr) -> None:
        self._stdscr = stdscr
        curses.curs_set(0)
        stdscr.keypad(True)

        self._check_terminal_size()
        self._show_splash(stdscr)
        self._game_loop(stdscr)

        if self._victory:
            self._show_victory(stdscr)
        else:
            self._show_quit_screen(stdscr)

    def _check_terminal_size(self) -> None:
        rows, cols = self._stdscr.getmaxyx()
        if rows < MIN_ROWS or cols < MIN_COLS:
            curses.endwin()
            raise TerminalTooSmallError(
                f"Terminal must be at least {MIN_COLS}x{MIN_ROWS} "
                f"(current: {cols}x{rows}). Please resize and try again."
            )

    def _show_splash(self, stdscr) -> None:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "*** TREASURE RUN ***"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title)

        self._draw_profile_block(stdscr, start_row=4)

        prompt = "Press any key to start..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt)
        stdscr.refresh()
        stdscr.getch()

    def _game_loop(self, stdscr) -> None:
        while True:
            if self._victory:
                break

            self._check_terminal_size()
            self._draw_screen(stdscr)
            key = stdscr.getch()

            if key in (ord("q"), ord("Q")):
                break

            if key in (ord("r"), ord("R")):
                self._engine.reset()
                self._steps = 0
                self._victory = False
                self._message = "Game reset to beginning."
                continue

            if key == ord(">"):
                self._handle_portal()
                continue

            direction = KEY_MAP.get(key)
            if direction is not None:
                self._handle_move(direction)

    def _handle_move(self, direction: Direction) -> None:
        before = self._engine.player.get_collected_count()
        try:
            self._engine.move_player(direction)
            self._steps += 1
            after = self._engine.player.get_collected_count()

            if after > before:
                delta = after - before
                noun = "treasure" if delta == 1 else "treasures"
                total = self._engine.get_total_treasure_count()
                self._message = (
                    f"You picked up {delta} {noun}! ({after}/{total})"
                )
                if self._engine.is_victory():
                    self._victory = True
            else:
                self._message = ""
        except ImpassableError:
            self._message = "You can't go that way."
        except GameEngineError as exc:
            self._message = f"Error: {exc}"

    def _handle_portal(self) -> None:
        before_room = self._engine.player.get_room()
        for direction in (
            Direction.NORTH,
            Direction.SOUTH,
            Direction.EAST,
            Direction.WEST,
        ):
            try:
                self._engine.move_player(direction)
                self._steps += 1
                after_room = self._engine.player.get_room()
                if after_room != before_room:
                    self._message = (
                        f"Entered room {after_room} through a portal!"
                    )
                    return
            except (ImpassableError, GameEngineError):
                continue
        self._message = "No portal reachable from here."

    def _draw_screen(self, stdscr) -> None:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()

        self._draw_header(stdscr, cols)
        self._draw_grid(stdscr, rows, cols)
        self._draw_legend(stdscr, cols)
        self._draw_statusbar(
            stdscr,
            rows,
            cols,
            self._engine.player.get_room(),
            self._engine.get_room_count(),
        )

        stdscr.refresh()

    def _draw_header(self, stdscr, cols: int) -> None:
        room_id = self._engine.player.get_room()
        room_count = self._engine.get_room_count()

        self._safe_addstr(stdscr, 0, 0, (self._message or "")[: cols - 1])
        self._safe_addstr(
            stdscr,
            1,
            0,
            f"Room {room_id}  |  {room_count} rooms in world"[: cols - 1],
        )

    def _draw_grid(self, stdscr, rows: int, cols: int) -> None:
        room_str = self._engine.render_current_room()
        for i, line in enumerate(room_str.split("\n")):
            if i >= rows - 5:
                break
            self._safe_addstr(stdscr, 2 + i, 0, line[: cols - 1])

    def _draw_legend(self, stdscr, cols: int) -> None:
        legend_col = 50
        if cols <= legend_col + 22:
            return

        self._safe_addstr(stdscr, 2, legend_col, "Game Elements:")
        self._safe_addstr(stdscr, 3, legend_col, "@ - player")
        self._safe_addstr(stdscr, 4, legend_col, "# - wall")
        self._safe_addstr(stdscr, 5, legend_col, "$ - gold")
        self._safe_addstr(stdscr, 6, legend_col, "x - portal")

    def _draw_statusbar(
        self, stdscr, rows: int, cols: int, room_id: int, room_count: int
    ) -> None:
        self._safe_addstr(
            stdscr,
            rows - 3,
            0,
            f"Game Controls: {CONTROLS}"[: cols - 1],
        )

        collected = self._engine.player.get_collected_count()
        total = self._engine.get_total_treasure_count()
        name = self._profile.get("player_name", "Player")

        status = (
            f"{name}  |  Gold: {collected}/{total}  |  "
            f"Steps: {self._steps}  |  Room: {room_id}/{room_count}"
        )
        self._safe_addstr(stdscr, rows - 2, 0, status[: cols - 1])

        footer_text = "rajvansh@uoguelph.com"
        self._safe_addstr(stdscr, rows - 1, 0, "Treasure Run")
        self._safe_addstr(
            stdscr,
            rows - 1,
            max(0, cols - len(footer_text) - 1),
            footer_text,
        )

    def _show_victory(self, stdscr) -> None:
        self._update_profile()
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "*** YOU WIN! ALL TREASURE COLLECTED! ***"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title)

        self._draw_profile_block(stdscr, start_row=4)

        total = self._engine.get_total_treasure_count()
        summary = (
            f"Treasures: {total}/{total}  |  "
            f"Steps: {self._steps}  |  "
            f"Room: {self._engine.player.get_room()}"
        )
        self._safe_addstr(stdscr, 11, 4, summary[: cols - 5])

        prompt = "Press any key to exit..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt)
        stdscr.refresh()
        stdscr.getch()

    def _show_quit_screen(self, stdscr) -> None:
        self._update_profile()

        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "--- GAME OVER ---"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title)

        self._draw_profile_block(stdscr, start_row=4)

        collected = self._engine.player.get_collected_count()
        run_line = (
            f"This run:  {collected} treasure(s) collected  |  "
            f"{self._steps} steps taken"
        )
        self._safe_addstr(stdscr, 11, 4, run_line[: cols - 5])

        prompt = "Press any key to exit..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt)
        stdscr.refresh()
        stdscr.getch()

    def _draw_profile_block(self, stdscr, start_row: int) -> None:
        profile = self._profile
        _, cols = stdscr.getmaxyx()

        lines = [
            f"Player             : {profile.get('player_name', 'Unknown')}",
            f"Games played       : {profile.get('games_played', 0)}",
            f"Max treasure       : {profile.get('max_treasure_collected', 0)}",
            f"Rooms completed    : {profile.get('most_rooms_world_completed', 0)}",
            f"Last played        : {profile.get('timestamp_last_played', 'never')}",
        ]

        for i, line in enumerate(lines):
            self._safe_addstr(stdscr, start_row + i, 4, line[: cols - 5])

    def _update_profile(self) -> None:
        collected = self._engine.player.get_collected_count()
        room_id = self._engine.player.get_room()

        self._profile["games_played"] = (
            self._profile.get("games_played", 0) + 1
        )
        self._profile["max_treasure_collected"] = max(
            self._profile.get("max_treasure_collected", 0), collected
        )
        self._profile["most_rooms_world_completed"] = max(
            self._profile.get("most_rooms_world_completed", 0), room_id
        )
        self._profile["timestamp_last_played"] = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            with open(self._profile_path, "w", encoding="utf-8") as profile_file:
                json.dump(self._profile, profile_file, indent=2)
        except OSError:
            pass

    @staticmethod
    def _safe_addstr(stdscr, row: int, col: int, text: str) -> None:
        try:
            stdscr.addstr(row, col, text)
        except curses.error:
            pass


def prompt_player_name(stdscr) -> str:
    """Prompt for player name when no profile file exists."""
    curses.echo()
    curses.curs_set(1)

    rows, cols = stdscr.getmaxyx()
    stdscr.clear()

    msg = "No profile found. Enter your player name:"
    stdscr.addstr(rows // 2 - 1, max(0, cols // 2 - len(msg) // 2), msg)
    stdscr.addstr(rows // 2, max(0, cols // 2 - 20), "> ")
    stdscr.refresh()

    name_bytes = stdscr.getstr(rows // 2, max(0, cols // 2 - 18), 40)

    curses.noecho()
    curses.curs_set(0)

    return name_bytes.decode("utf-8").strip() or "Player"