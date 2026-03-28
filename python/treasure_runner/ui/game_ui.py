"""
GameUI: Curses-based view for Treasure Run.

Handles all rendering, input, and screen layout.
The controller (GameEngine) is queried for state; this class
never touches ctypes or C pointers directly.
"""

#imports
import curses
import json
from datetime import datetime, timezone
from typing import Optional
from time import time

from ..models.exceptions import ImpassableError, GameEngineError
from ..bindings import Direction


#minimum termal reqirements
MIN_ROWS = 24
MIN_COLS = 80

#ampping keys
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

#sting for the info on how ot play the game
CONTROLS = "Arrows/WASD: move  >: portal  r: reset  q: quit"


# Colour pair indices  (initialised in _init_colors)

CP_DEFAULT   = 0   # curses default
CP_HEADER    = 1   # cyanish     on black         - header bar
CP_WALL      = 2   #  blue on black                 - # walls
CP_PLAYER    = 3   # yellow cloest to gold on black  - @ player
CP_GOLD      = 4   # yellow on black                 - $ gold
CP_PORTAL    = 5   # magnta/red on black             - X portals
CP_FLOOR     = 6   # white on black                   - dots / open space
CP_LEGEND_HD = 7   # light blue on black              - legend heading
CP_STATUS    = 8   # green on black                   - status bar
CP_CONTROLS  = 9   # white on black                  - controls bar
CP_MSG       = 10  # yellow on black                 - in-game messages
CP_MAP_CUR   = 11  # black on green                   - current room node
CP_MAP_VIS   = 12  # black on cyan                  - visited room node
CP_MAP_UNVIS = 13  # black on white                    - unvisited room node
CP_MAP_EDGE  = 14  # white on black                     - minimap edges
CP_WIN_TITLE = 15  # black on yellow                    - victory / game-over title


class TerminalTooSmallError(Exception):
    """Raised when the terminal is too small to display the game."""






class GameUI:
    """Curses view for Treasure Run."""


    # ------------------
    # Treasure tracking
    # ------------------

    def get_total_treasure_count(self) -> int:
        """Returns the total treasure count, computed once at init."""
        return self._total_treasure_count

    def is_victory(self) -> bool:
        """Returns True if player collected all treasure (and there is treasure)."""
        total = self.get_total_treasure_count()
        return total > 0 and self._engine.player.get_collected_count() == total

    # -------------
    # Construction
    # -----------------------------------------


    def __init__(self, engine, profile: dict, profile_path: str):
        self._engine = engine
        self._profile = profile
        self._profile_path = profile_path
        self._message = "Welcome! Use arrows or WASD to move."
        self._steps = 0
        self._stdscr: Optional["curses._CursesWindow"] = None
        self._victory = False
        self._start_time = None

        # World graph data - built once by _explore_world()
        self._room_ids: list[int] = []
        self._adj: dict[int, set[int]] = {}        # adjacency matrix as dict of sets
        self._room_has_treasure: dict[int, bool] = {}
        self._visited_rooms: set[int] = set()

        self._total_treasure_count = self._explore_world()

    def _try_move(self, direction: Direction) -> bool:
        """
        Attempt one engine move.
        Returns True if the player entered a new room, False otherwise.
        Swallows ImpassableError / GameEngineError so callers stay branch-free.
        """
        try:
            self._engine.move_player(direction)
            return True
        except (ImpassableError, GameEngineError):
            return False

    def _reset_engine_safe(self) -> None:
        """Reset the engine, silently ignoring errors (used during world exploration)."""
        try:
            self._engine.reset()
        except (AttributeError, GameEngineError):
            pass
    def _explore_world(self) -> int:
        """
        Walk every reachable room once to:
          - Count '$' tiles (treasure total).
          - Build an adjacency matrix (dict of sets) for the minimap.
          - Record which rooms contain treasure.
        Resets the engine before AND after so the player starts fresh.
        Returns the total treasure count.
        """
        total_gold = 0
        try:
            self._engine.reset()
            self._room_ids = self._engine.get_room_ids()
            n = len(self._room_ids)

            self._adj = {rid: set() for rid in self._room_ids}
            self._room_has_treasure = {rid: False for rid in self._room_ids}

            visited: set[int] = set()

            def visit_current() -> None:
                nonlocal total_gold
                rid = self._engine.player.get_room()
                if rid in visited:
                    return
                render = self._engine.render_current_room()
                gold = render.count("$")
                total_gold += gold
                self._room_has_treasure[rid] = gold > 0
                visited.add(rid)

            visit_current()

            # BFS-style walk until all rooms discovered
            for _ in range(n * 100):
                if len(visited) == n:
                    break
                current = self._engine.player.get_room()

                for direction in (Direction.NORTH, Direction.SOUTH,
                                  Direction.EAST, Direction.WEST):
                    if not self._try_move(direction):
                        continue
                    neighbour = self._engine.player.get_room()
                    if neighbour != current:
                        self._adj[current].add(neighbour)
                        self._adj[neighbour].add(current)
                        visit_current()

                # also try portal repeatedly to reach all connected rooms
                for _ in range(10):
                    try:
                        current = self._engine.player.get_room()
                        self._engine.game_engine_try_portal()
                        neighbour = self._engine.player.get_room()
                        if neighbour != current:
                            self._adj[current].add(neighbour)
                            self._adj[neighbour].add(current)
                            visit_current()
                    except (ImpassableError, GameEngineError):
                        pass

        except (AttributeError, GameEngineError):
            total_gold = 0
        finally:
            self._reset_engine_safe()

        total_gold= total_gold+1
        return total_gold

    # ---------------------------------------------
    # Curses entry point
    # -----------------------------------------------------------

    def run(self) -> None:
        curses.wrapper(self._main)

    def _main(self, stdscr) -> None:
        self._stdscr = stdscr
        curses.curs_set(0)
        stdscr.keypad(True)
        self._init_colors()

        self._start_time = time()

        self._check_terminal_size()
        self._show_splash(stdscr)

        self._game_loop(stdscr)

        if self._victory:
            self._show_victory(stdscr)
        else:
            self._show_quit_screen(stdscr)

    # ------------
    # Colour initialisation
    # -----------------------------------

    @staticmethod
    def _init_colors() -> None:
        if not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(CP_HEADER,    curses.COLOR_CYAN,    -1)
        curses.init_pair(CP_WALL,      curses.COLOR_BLUE,    -1)
        curses.init_pair(CP_PLAYER,    curses.COLOR_YELLOW,  -1)
        curses.init_pair(CP_GOLD,      curses.COLOR_YELLOW,  -1)
        curses.init_pair(CP_PORTAL,    curses.COLOR_MAGENTA, -1)
        curses.init_pair(CP_FLOOR,     curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_LEGEND_HD, curses.COLOR_CYAN,    -1)
        curses.init_pair(CP_STATUS,    curses.COLOR_GREEN,   -1)
        curses.init_pair(CP_CONTROLS,  curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_MSG,       curses.COLOR_YELLOW,  -1)
        curses.init_pair(CP_MAP_CUR,   curses.COLOR_BLACK,   curses.COLOR_GREEN)
        curses.init_pair(CP_MAP_VIS,   curses.COLOR_BLACK,   curses.COLOR_CYAN)
        curses.init_pair(CP_MAP_UNVIS, curses.COLOR_BLACK,   curses.COLOR_WHITE)
        curses.init_pair(CP_MAP_EDGE,  curses.COLOR_WHITE,   -1)
        curses.init_pair(CP_WIN_TITLE, curses.COLOR_BLACK,   curses.COLOR_YELLOW)


        #to make the portal color mtch the room walls

        curses.init_pair(20, curses.COLOR_BLUE, -1)
        curses.init_pair(21, curses.COLOR_GREEN, -1)
        curses.init_pair(22, curses.COLOR_MAGENTA, -1)
        curses.init_pair(23, curses.COLOR_CYAN, -1)




    # -------------------------------
    # Helpers
    # ----------------------------------------

    def _check_terminal_size(self) -> None:
        rows, cols = self._stdscr.getmaxyx()
        if rows < MIN_ROWS or cols < MIN_COLS:
            curses.endwin()
            raise TerminalTooSmallError(
                f"Terminal must be at least {MIN_COLS}x{MIN_ROWS} "
                f"(current: {cols}x{rows}). Please resize and try again."
            )

    @staticmethod
    def _safe_addstr(stdscr, row: int, col: int, text: str,
                     attr: int = 0) -> None:
        try:
            stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass

    @staticmethod
    def _color(pair: int, bold: bool = False) -> int:
        attr = curses.color_pair(pair)
        if bold:
            attr |= curses.A_BOLD
        return attr

    # -----------------------------------
    # Splash screen
    # ------------------------

    def _show_splash(self, stdscr) -> None:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "*** TREASURE RUN ***"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title,
                          self._color(CP_WIN_TITLE, bold=True))

        self._draw_profile_block(stdscr, start_row=4)

        prompt = "Press any key to start..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt,
                          self._color(CP_CONTROLS))
        stdscr.refresh()
        stdscr.getch()

    # ------------------
    # Game loop
    # ---------------------------------------

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
                self._visited_rooms.clear()
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
            self._visited_rooms.add(self._engine.player.get_room())
            after = self._engine.player.get_collected_count()

            if after > before:
                delta = after - before
                noun = "treasure" if delta == 1 else "treasures"
                total = self.get_total_treasure_count()
                self._message = (
                    f"You picked up {delta} {noun}! ({after}/{total})"
                )
                if self.is_victory():
                    self._victory = True
                    self._message = "All treasure collected! You win!"
            else:
                self._message = ""

        except ImpassableError:
            self._message = "You can't go that way."
        except GameEngineError as exc:
            self._message = f"Error: {exc}"

    def _handle_portal(self) -> None:
        before_room = self._engine.player.get_room()
        for direction in (Direction.NORTH, Direction.SOUTH,
                          Direction.EAST, Direction.WEST):
            try:
                self._engine.game_engine_try_portal()
                self._steps += 1
                after_room = self._engine.player.get_room()
                self._visited_rooms.add(after_room)

                if after_room != before_room:
                    self._message = (
                        f"Entered room {after_room} through a portal!"
                    )
                    return

            except (ImpassableError, GameEngineError):
                continue

        self._message = "No portal reachable from here."

    # -------------
    # Main screen drawing
    # ----------------------------

    def _draw_screen(self, stdscr) -> None:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()

        # Always mark the current room as visited
        self._visited_rooms.add(self._engine.player.get_room())

        self._draw_header(stdscr, cols)
        self._draw_grid(stdscr, rows, cols)
        self._draw_right_panel(stdscr, rows, cols)
        self._draw_statusbar(
            stdscr, rows, cols,
            self._engine.player.get_room(),
            self._engine.get_room_count(),
        )

        stdscr.refresh()

    def _draw_header(self, stdscr, cols: int) -> None:
        collected = self._engine.player.get_collected_count()
        total = self.get_total_treasure_count()
        progress = f"{collected}/{total} treasures"
        message = self._message or ""
        full_message = f"{message}  |  {progress}" if message else progress

        room_id = self._engine.player.get_room()
        room_count = self._engine.get_room_count()

        self._safe_addstr(stdscr, 0, 0, full_message[: cols - 1],
                          self._color(CP_MSG, bold=True))
        self._safe_addstr(
            stdscr, 1, 0,
            f"Room {room_id + 1}  |  {room_count} rooms in world"[: cols - 1],
            self._color(CP_HEADER),
        )

    def _char_attr(self, char: str, wall_color: int,
                   neighbours: list, portal_index: int) -> int:
        """Return the curses attribute for a single room character."""
        if char == "#":
            return self._color(wall_color, bold=True)
        if char == "@":
            return self._color(CP_PLAYER, bold=True)
        if char == "$":
            return self._color(CP_GOLD, bold=True)
        if char in ("X", "x"):
            if portal_index < len(neighbours):
                portal_color = 20 + (neighbours[portal_index] % 4)
            else:
                portal_color = CP_PORTAL
            return self._color(portal_color, bold=True)
        return self._color(CP_FLOOR)

    def _draw_grid(self, stdscr, rows: int, cols: int) -> None:
        """Render the current room with per-character colouring."""
        grid_max_col = 48

        # Pre-compute room-level values once, outside the character loop
        room_str = self._engine.render_current_room()
        room_id = self._engine.player.get_room()
        neighbours = list(self._adj.get(room_id, []))
        wall_color = 20 + (room_id % 3)
        portal_index = 0

        for i, line in enumerate(room_str.split("\n")):
            if i >= rows - 5:
                break
            screen_row = 2 + i
            for j, char in enumerate(line):
                if j >= grid_max_col - 1:
                    break
                attr = self._char_attr(char, wall_color, neighbours, portal_index)
                if char in ("X", "x"):
                    portal_index += 1
                self._safe_addstr(stdscr, screen_row, j, char, attr)

    # ----------------------------------
    # Right panel  (legend + minimap)
    # ---------------------------------------

    PANEL_COL     = 50   # left edge of the right panel
    MAP_ROOMS_PER_ROW = 3
    MAP_NODE_WIDTH    = 5   # "[NN]" + 1 gap
    MAP_TOP_ROW       = 14

    def _draw_right_panel(self, stdscr, rows: int, cols: int) -> None:
        if cols <= self.PANEL_COL + 22:
            return
        self._draw_legend(stdscr)
        self._draw_minimap(stdscr, cols)

    def _draw_legend_elements(self, stdscr, start_row: int) -> int:
        """Draw the tile-type legend entries. Returns the next free row."""
        col = self.PANEL_COL
        row = start_row
        room_id = self._engine.player.get_room()

        # Static entries
        static_entries = [
            ("@", " player",                   CP_PLAYER),
            ("#", f" room {room_id + 1} wall", 20 + (room_id % 4)),
            ("$", " gold",                     CP_GOLD),
        ]
        for symbol, label, pair in static_entries:
            self._safe_addstr(stdscr, row, col,     symbol, self._color(pair, bold=True))
            self._safe_addstr(stdscr, row, col + 1, label,  self._color(CP_FLOOR))
            row += 1

        # One entry per portal destination from adjacency map
        neighbours = sorted(self._adj.get(room_id, []))
        for neighbour in neighbours:
            portal_color = 20 + (neighbour % 4)
            self._safe_addstr(stdscr, row, col,     "x",
                            self._color(portal_color, bold=True))
            self._safe_addstr(stdscr, row, col + 1, f" portal to room {neighbour + 1}",
                            self._color(CP_FLOOR))
            row += 1

        return row

    def _draw_legend_map_key(self, stdscr, start_row: int) -> None:
        """Draw the minimap colour-key entries."""
        col = self.PANEL_COL
        row = start_row
        map_key = [
            ("[R]", " you are here",  CP_MAP_CUR),
            ("[R]", " visited",       CP_MAP_VIS),
            ("[R]", " unvisited",     CP_MAP_UNVIS),
        ]
        for symbol, label, pair in map_key:
            self._safe_addstr(stdscr, row, col,
                              symbol, self._color(pair, bold=True))
            self._safe_addstr(stdscr, row, col + len(symbol),
                              label,  self._color(CP_FLOOR))
            row += 1

    def _draw_legend(self, stdscr) -> None:
        col = self.PANEL_COL
        row = 2

        self._safe_addstr(stdscr, row, col, "Game Elements:",
                          self._color(CP_LEGEND_HD, bold=True))
        row = self._draw_legend_elements(stdscr, start_row=row + 1)

        row += 1
        self._safe_addstr(stdscr, row, col, "Map Key:",
                          self._color(CP_LEGEND_HD, bold=True))
        self._draw_legend_map_key(stdscr, start_row=row + 1)

    def _minimap_slot(self, sorted_ids: list) -> dict:
        """Map each room_id to its (map_row, map_col) display slot."""
        return {
            rid: (idx // self.MAP_ROOMS_PER_ROW, idx % self.MAP_ROOMS_PER_ROW)
            for idx, rid in enumerate(sorted_ids)
        }

    def _draw_minimap_node(self, stdscr, rid: int, current_room: int,
                           screen_row: int, screen_col: int) -> str:
        """Draw a single room node; returns the label string."""
        label = f"[{rid + 1:1d}]"
        if rid == current_room:
            node_attr = self._color(CP_MAP_CUR,   bold=True)
        elif rid in self._visited_rooms:
            node_attr = self._color(CP_MAP_VIS,   bold=True)
        else:
            node_attr = self._color(CP_MAP_UNVIS, bold=True)
        self._safe_addstr(stdscr, screen_row, screen_col, label, node_attr)

        # Treasure indicator below node
        if self._room_has_treasure.get(rid, False):
            self._safe_addstr(stdscr, screen_row + 1, screen_col + 1, "$",
                              self._color(CP_GOLD, bold=True))
        return label

    def _draw_minimap_edges(self, stdscr, rid: int, sorted_ids: list,
                            slot: dict, map_row: int, map_col: int,
                            screen_row: int, screen_col: int, label: str) -> None:
        """Draw horizontal and vertical edges for one minimap node."""
        num_rooms = len(sorted_ids)
        idx = sorted_ids.index(rid)

        #  Horizontal edge to the right neighbour (same map row)
        if map_col < self.MAP_ROOMS_PER_ROW - 1 and idx + 1 < num_rooms:
            right_rid = sorted_ids[idx + 1]
            right_map_row, _ = slot[right_rid]
            if right_map_row == map_row:
                edge = "-" if right_rid in self._adj.get(rid, set()) else " "
                self._safe_addstr(stdscr, screen_row,
                                  screen_col + len(label), edge,
                                  self._color(CP_MAP_EDGE))

        #  Vertical edge to neighbour in the row below
        for nid in self._adj.get(rid, set()):
            nmap_row, nmap_col = slot[nid]
            if nmap_row == map_row + 1 and nmap_col == map_col:
                self._safe_addstr(stdscr, screen_row + 1, screen_col + 1, "|",
                                  self._color(CP_MAP_EDGE))

    def _draw_minimap(self, stdscr, cols: int) -> None:
        """
        Draw a node-graph minimap built from the adjacency matrix.

        Rooms are laid out in a snake grid (up to MAP_ROOMS_PER_ROW per row).
        Each node is labelled [N] and colour-coded:
          green  = current room
          cyan   = visited
          white  = unvisited
        Horizontal edges are drawn as '-', vertical edges as '|'.
        A '$' below a node means that room still has uncollected treasure.
        """
        if not self._room_ids or cols <= self.PANEL_COL + 22:
            return

        current_room = self._engine.player.get_room()
        sorted_ids = sorted(self._room_ids)
        slot = self._minimap_slot(sorted_ids)
        map_left = self.PANEL_COL

        # Section title
        self._safe_addstr(stdscr, self.MAP_TOP_ROW - 1, map_left, "World Map:",
                          self._color(CP_LEGEND_HD, bold=True))

        for rid in sorted_ids:
            map_row, map_col = slot[rid]
            screen_row = self.MAP_TOP_ROW + map_row * 2   # 2 rows per map-row
            screen_col = map_left + map_col * self.MAP_NODE_WIDTH

            label = self._draw_minimap_node(
                stdscr, rid, current_room, screen_row, screen_col
            )
            self._draw_minimap_edges(
                stdscr, rid, sorted_ids, slot,
                map_row, map_col, screen_row, screen_col, label
            )

    # -----------------
    # Status bar
    # ----------------------------------------

    def _build_status_line(self, room_id: int, room_count: int) -> str:
        """Compose the status bar text from current game state."""
        name = self._profile.get("player_name", "Player")
        collected = self._engine.player.get_collected_count()
        total = self.get_total_treasure_count()
        return (
            f"{name}  |  Gold: {collected}/{total}  |  "
            f"Steps: {self._steps}  |  Room: {room_id + 1}/{room_count}"
        )

    def _draw_statusbar(
        self, stdscr, rows: int, cols: int, room_id: int, room_count: int
    ) -> None:
        self._safe_addstr(
            stdscr, rows - 3, 0,
            f"Game Controls: {CONTROLS}"[: cols - 1],
            self._color(CP_CONTROLS),
        )

        status = self._build_status_line(room_id, room_count)
        self._safe_addstr(stdscr, rows - 2, 0, status[: cols - 1],
                          self._color(CP_STATUS, bold=True))

        footer_text = "rajvansh@uoguelph.com"
        self._safe_addstr(stdscr, rows - 1, 0, "Treasure Run",
                          self._color(CP_HEADER))
        self._safe_addstr(
            stdscr, rows - 1,
            max(0, cols - len(footer_text) - 1),
            footer_text,
            self._color(CP_HEADER),
        )

    # -----------------------------------------------------------------------
    # Victory / quit screens
    # -----------------------------------------------------------------------

    def _build_victory_summary(self) -> str:
        """Compose the one-line victory stats string."""
        total = self.get_total_treasure_count()
        collected = self._engine.player.get_collected_count()
        room = self._engine.player.get_room()
        return (
            f"Treasures: {collected}/{total}  |  "
            f"Steps: {self._steps}  |  Final Room: {room}"
        )

    def _show_victory(self, stdscr) -> None:
        self._update_profile()
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "*** YOU WIN! ALL TREASURE COLLECTED! ***"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title,
                          self._color(CP_WIN_TITLE, bold=True))

        self._draw_profile_block(stdscr, start_row=4)

        summary = self._build_victory_summary()
        self._safe_addstr(stdscr, 11, 4, summary[: cols - 5],
                          self._color(CP_STATUS, bold=True))

        if self._start_time is not None:
            elapsed = int(time() - self._start_time)
            self._safe_addstr(stdscr, 12, 4,
                              f"Time elapsed: {elapsed} seconds"[: cols - 5],
                              self._color(CP_HEADER))

        prompt = "Press any key to exit..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt,
                          self._color(CP_CONTROLS))
        stdscr.refresh()
        stdscr.getch()

    def _show_quit_screen(self, stdscr) -> None:
        self._update_profile()
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        mid = cols // 2

        title = "--- GAME OVER ---"
        self._safe_addstr(stdscr, 2, mid - len(title) // 2, title,
                          self._color(CP_WIN_TITLE, bold=True))

        self._draw_profile_block(stdscr, start_row=4)

        collected = self._engine.player.get_collected_count()
        run_line = (
            f"This run:  {collected} treasure(s) collected  |  "
            f"{self._steps} steps taken"
        )
        self._safe_addstr(stdscr, 11, 4, run_line[: cols - 5],
                          self._color(CP_STATUS))

        prompt = "Press any key to exit..."
        self._safe_addstr(stdscr, rows - 2, mid - len(prompt) // 2, prompt,
                          self._color(CP_CONTROLS))
        stdscr.refresh()
        stdscr.getch()

    # -----------------------------------------------------------------------
    # Profile helpers
    # -----------------------------------------------------------------------

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
            self._safe_addstr(stdscr, start_row + i, 4, line[: cols - 5],
                              self._color(CP_FLOOR))

    def _update_profile(self) -> None:
        collected = self._engine.player.get_collected_count()
        room_id   = self._engine.player.get_room()

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
            with open(self._profile_path, "w", encoding="utf-8") as f:
                json.dump(self._profile, f, indent=2)
        except OSError:
            pass

    # -----------------------------------------------------------------------
    # Static helper
    # -----------------------------------------------------------------------

    @staticmethod
    def _safe_addstr(stdscr, row: int, col: int, text: str,
                     attr: int = 0) -> None:
        try:
            stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass


# ---------------------------------------------------------------------------
# Standalone helper
# ---------------------------------------------------------------------------

def prompt_player_name(stdscr) -> str:
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