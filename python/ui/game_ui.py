"""
GameUI: Curses-based view for Treasure Run.

Handles all rendering, input, and screen layout.
The controller (GameEngine) is queried for state; this class
never touches ctypes or C pointers directly.

"""

import curses
import json
from datetime import datetime, timezone

from ..models.exceptions import ImpassableError, GameEngineError
from ..bindings import Direction


MIN_ROWS = 24  # minimum rows needed for proper display
MIN_COLS = 80  # minimum columns needed

# mapping keyboard inputs to directions (so user can use arrows or WASD)
KEY_MAP = {
    curses.KEY_UP:    Direction.NORTH,
    ord('w'):         Direction.NORTH,
    ord('W'):         Direction.NORTH,
    curses.KEY_DOWN:  Direction.SOUTH,
    ord('s'):         Direction.SOUTH,
    ord('S'):         Direction.SOUTH,
    curses.KEY_RIGHT: Direction.EAST,
    ord('d'):         Direction.EAST,
    ord('D'):         Direction.EAST,
    curses.KEY_LEFT:  Direction.WEST,
    ord('a'):         Direction.WEST,
    ord('A'):         Direction.WEST,
}

# controls string shown on screen
CONTROLS = "Arrows/WASD: move  >: portal  r: reset  q: quit"


class TerminalTooSmallError(Exception):
    """Raised when the terminal is too small to display the game."""


class GameUI:
    """Curses view for Treasure Run."""

    def __init__(self, engine, profile: dict, profile_path: str):
        # engine handles game logic, UI just calls it
        self._engine = engine
        self._profile = profile          # player stats
        self._profile_path = profile_path  # where we save profile
        self._message = "Welcome! Use arrows or WASD to move."
        self._steps = 0       # count number of moves
        self._stdscr = None   # set properly in _main each run

    # start the UI using curses
    def run(self) -> None:
        """Launch the curses wrapper and start the game."""
        curses.wrapper(self._main)

    # main curses function (everything runs from here)
    def _main(self, stdscr) -> None:
        self._stdscr = stdscr  # update reference each run
        curses.curs_set(0)     # hide cursor
        stdscr.keypad(True)    # allow arrow keys

        self._check_terminal_size()
        self._show_splash(stdscr)
        self._game_loop(stdscr)
        self._show_quit_screen(stdscr)

    # check if terminal is big enough
    def _check_terminal_size(self) -> None:
        rows, cols = self._stdscr.getmaxyx()
        if rows < MIN_ROWS or cols < MIN_COLS:
            curses.endwin()  # exit curses mode first
            raise TerminalTooSmallError(
                f"Terminal must be at least {MIN_COLS}x{MIN_ROWS} "
                f"(current: {cols}x{rows}). Please resize and try again."
            )

    # splash / start screen
    def _show_splash(self, stdscr) -> None:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "*** TREASURE RUN ***"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title)

        # show profile info here
        self._draw_profile_block(stdscr, start_row=4)

        prompt = "Press any key to start..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt)
        stdscr.refresh()
        stdscr.getch()  # wait for user input

    # main loop where game keeps running
    def _game_loop(self, stdscr) -> None:
        while True:
            self._check_terminal_size()
            self._draw_screen(stdscr)
            key = stdscr.getch()

            if key in (ord('q'), ord('Q')):
                break  # quit game

            if key in (ord('r'), ord('R')):
                # reset game state
                self._engine.reset()
                self._steps = 0
                self._message = "Game reset to beginning."
                continue

            if key == ord('>'):
                self._handle_portal()
                continue

            # check movement keys
            direction = KEY_MAP.get(key)
            if direction is not None:
                self._handle_move(direction)

    # handles movement input
    def _handle_move(self, direction: Direction) -> None:
        before = self._engine.player.get_collected_count()
        try:
            self._engine.move_player(direction)
            self._steps += 1
            after = self._engine.player.get_collected_count()
            #check if treasure collected
            if after > before:
                delta = after - before
                noun = "treasure" if delta == 1 else "treasures"
                self._message = f"You picked up {delta} {noun}!"
                # check victory after every collection
                if self._engine.is_victory():
                    self._show_victory(self._stdscr)
            else:
                self._message = ""
        except ImpassableError:
            self._message = "You can't go that way."
        except GameEngineError as exc:
            self._message = f"Error: {exc}"

    # try to move through portal
    def _handle_portal(self) -> None:
        before_room = self._engine.player.get_room()
        for direction in (Direction.NORTH, Direction.SOUTH,
                          Direction.EAST, Direction.WEST):
            try:
                self._engine.move_player(direction)
                self._steps += 1
                after_room = self._engine.player.get_room()
                if after_room != before_room:
                    self._message = f"Entered room {after_room} through a portal!"
                    return
            except (ImpassableError, GameEngineError):
                continue
        self._message = "No portal reachable from here."

    # draw everything on screen
    def _draw_screen(self, stdscr) -> None:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        room_id = self._engine.player.get_room()
        room_count = self._engine.get_room_count()

        # message bar (top)
        self._safe_addstr(stdscr, 0, 0, (self._message or "")[:cols - 1])

        # room info
        self._safe_addstr(stdscr, 1, 0,
            f"Room {room_id}  |  {room_count} rooms in world"[:cols - 1])

        # draw map/grid, legend, and status bar
        self._draw_grid(stdscr, rows, cols)
        self._draw_legend(stdscr, cols)
        self._draw_statusbar(stdscr, rows, cols, room_id, room_count)

        stdscr.refresh()

    # draw the room grid
    def _draw_grid(self, stdscr, rows: int, cols: int) -> None:
        room_str = self._engine.render_current_room()
        for i, line in enumerate(room_str.split("\n")):
            if i >= rows - 5:
                break
            self._safe_addstr(stdscr, 2 + i, 0, line[:cols - 1])

    def _draw_legend(self, stdscr, cols: int) -> None:
        legend_col = 50
        if cols <= legend_col + 22:
            return
        self._safe_addstr(stdscr, 2, legend_col, "Game Elements:")
        self._safe_addstr(stdscr, 3, legend_col, "@ - player")
        self._safe_addstr(stdscr, 4, legend_col, "# - wall")
        self._safe_addstr(stdscr, 5, legend_col, "$ - gold")
        self._safe_addstr(stdscr, 6, legend_col, "x - open portal")
        self._safe_addstr(stdscr, 7, legend_col, "+ - locked portal")  # NEW
        self._safe_addstr(stdscr, 8, legend_col, "^ - switch plate")   # NEW

    def _draw_statusbar(self, stdscr, rows: int, cols: int,
                    room_id: int, room_count: int) -> None:
        # controls info
        self._safe_addstr(stdscr, rows - 3, 0,
            f"Game Controls: {CONTROLS}"[:cols - 1])

        # player status bar with treasure progress
        collected = self._engine.player.get_collected_count()
        total = self._engine.get_total_treasure_count()  # NEW
        name = self._profile.get("player_name", "Player")
        status = (f"{name}  |  Gold: {collected}/{total}  |  "
                f"Steps: {self._steps}  |  Room: {room_id}/{room_count}")
        self._safe_addstr(stdscr, rows - 2, 0, status[:cols - 1])

        footer_right = "rajvansh@uoguelph.com"
        self._safe_addstr(stdscr, rows - 1, 0, "Treasure Run")
        self._safe_addstr(stdscr, rows - 1,
            max(0, cols - len(footer_right) - 1), footer_right)

    # quit / game over screen
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
        self._safe_addstr(stdscr, 11, 4, run_line[:cols - 5])

        prompt = "Press any key to exit..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt)
        stdscr.refresh()
        stdscr.getch()

    # draw profile info block
    def _draw_profile_block(self, stdscr, start_row: int) -> None:
        prof = self._profile  # local alias for readability
        _, cols = stdscr.getmaxyx()
        lines = [
            f"Player             : {prof.get('player_name', 'Unknown')}",
            f"Games played       : {prof.get('games_played', 0)}",
            f"Max treasure       : {prof.get('max_treasure_collected', 0)}",
            f"Rooms completed    : {prof.get('most_rooms_world_completed', 0)}",
            f"Last played        : {prof.get('timestamp_last_played', 'never')}",
        ]
        for i, line in enumerate(lines):
            self._safe_addstr(stdscr, start_row + i, 4, line[:cols - 5])

    # update stats after game ends
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
        self._profile["timestamp_last_played"] = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        try:
            with open(self._profile_path, "w", encoding="utf-8") as profile_file:
                json.dump(self._profile, profile_file, indent=2)
        except OSError:
            pass  # ignore error, not super critical

    # helper to safely write text (avoids crash at edges)
    @staticmethod
    def _safe_addstr(stdscr, row: int, col: int, text: str) -> None:
        try:
            stdscr.addstr(row, col, text)
        except curses.error:
            pass


    # ask user for name if no profile exists
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

        # return name or default if empty
        return name_bytes.decode("utf-8").strip() or "Player"


    #new extension feature
        # victory screen shown when all treasure is collected
    def _show_victory(self, stdscr) -> None:
        self._update_profile()
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "*** YOU WIN! ALL TREASURE COLLECTED! ***"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title)

        self._draw_profile_block(stdscr, start_row=4)

        total = self._engine.get_total_treasure_count()
        summary = (f"Treasures: {total}/{total}  |  "
                f"Steps: {self._steps}  |  "
                f"Room: {self._engine.player.get_room()}")
        self._safe_addstr(stdscr, 11, 4, summary[:cols - 5])

        prompt = "Press any key to exit..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt)
        stdscr.refresh()
        stdscr.getch()

        # raise to break out of the game loop
        raise GameEngineError("victory")