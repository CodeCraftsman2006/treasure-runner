import { useState } from "react";

export default function StartScreen({ onStart, loading, error }) {
  const [name, setName] = useState("");

  const submit = (event) => {
    event.preventDefault();
    onStart(name.trim() || "Player");
  };

  return (
    <div className="app start-screen">
      <div className="start-card">
        <p className="eyebrow">Grid puzzle adventure</p>
        <h1>Treasure Runner</h1>
        <p className="subtitle">
          Explore rooms, push boulders, collect every treasure, and escape through portals.
        </p>

        <form onSubmit={submit}>
          <label htmlFor="player-name">Your name</label>
          <input
            id="player-name"
            type="text"
            maxLength={32}
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
          <button type="submit" className="btn primary" disabled={loading}>
            {loading ? "Loading world..." : "Start Game"}
          </button>
        </form>

        {error && <p className="error">{error}</p>}

        <p className="hint">
          Share this page with classmates — everyone gets their own game session.
        </p>
      </div>
    </div>
  );
}
