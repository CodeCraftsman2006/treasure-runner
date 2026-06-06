const TILE_CLASS = {
  "#": "wall",
  ".": "floor",
  "@": "player",
  $: "treasure",
  X: "portal",
  x: "portal",
};

function tileClass(char, roomId) {
  if (char === "#") {
    const variants = ["wall-a", "wall-b", "wall-c"];
    return variants[roomId % 3];
  }
  return TILE_CLASS[char] || "floor";
}

export default function GameBoard({ state, onMove, disabled }) {
  if (!state?.tiles?.length) {
    return <div className="board loading-board">Loading room...</div>;
  }

  const { tiles, room_id: roomId } = state;

  return (
    <div className="board-wrap">
      <div
        className="board"
        style={{
          gridTemplateColumns: `repeat(${tiles[0].length}, 2rem)`,
          gridTemplateRows: `repeat(${tiles.length}, 2rem)`,
        }}
      >
        {tiles.map((row, y) =>
          row.map((char, x) => (
            <button
              key={`${x}-${y}`}
              type="button"
              className={`tile ${tileClass(char, roomId)}`}
              disabled={disabled}
              aria-label={`tile ${x},${y}`}
              onClick={() => {
                const px = state.player_x;
                const py = state.player_y;
                if (x === px && y < py) onMove("north");
                else if (x === px && y > py) onMove("south");
                else if (y === py && x < px) onMove("west");
                else if (y === py && x > px) onMove("east");
              }}
            >
              {char === "#" ? "" : char === "." ? "·" : char}
            </button>
          )),
        )}
      </div>
    </div>
  );
}
