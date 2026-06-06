export default function HUD({ state, error }) {
  if (!state) return null;

  return (
    <div className="hud">
      <div className="hud-row">
        <span className="stat">
          Room <strong>{state.room_id + 1}</strong> / {state.room_count}
        </span>
        <span className="stat">
          Treasures <strong>{state.treasures_collected}</strong> / {state.total_treasures}
        </span>
        <span className="stat">
          Steps <strong>{state.steps}</strong>
        </span>
      </div>
      <p className={`message ${error ? "error" : ""}`}>
        {error || state.message || "Find every treasure to win!"}
      </p>
    </div>
  );
}
