import { useCallback, useEffect, useState } from "react";
import * as api from "./api";
import StartScreen from "./components/StartScreen";
import GameBoard from "./components/GameBoard";
import HUD from "./components/HUD";
import Minimap from "./components/Minimap";
import VictoryModal from "./components/VictoryModal";
import TouchControls from "./components/TouchControls";

const KEY_TO_DIRECTION = {
  ArrowUp: "north",
  ArrowDown: "south",
  ArrowLeft: "west",
  ArrowRight: "east",
  w: "north",
  W: "north",
  s: "south",
  S: "south",
  a: "west",
  A: "west",
  d: "east",
  D: "east",
};

export default function App() {
  const [screen, setScreen] = useState("start");
  const [sessionId, setSessionId] = useState(null);
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const startGame = async (playerName) => {
    setLoading(true);
    setError("");
    try {
      const result = await api.createGame(playerName);
      setSessionId(result.session_id);
      setState(result.state);
      setScreen("game");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const applyAction = useCallback(
    async (action) => {
      if (!sessionId || loading || state?.victory) return;
      setLoading(true);
      setError("");
      try {
        const result = await action();
        setState(result.state);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, loading, state?.victory],
  );

  const handleMove = useCallback(
    (direction) => applyAction(() => api.move(sessionId, direction)),
    [applyAction, sessionId],
  );

  const handlePortal = useCallback(
    () => applyAction(() => api.portal(sessionId)),
    [applyAction, sessionId],
  );

  const handleReset = useCallback(
    () => applyAction(() => api.resetGame(sessionId)),
    [applyAction, sessionId],
  );

  useEffect(() => {
    if (screen !== "game") return;

    const onKeyDown = (event) => {
      if (event.key === "r" || event.key === "R") {
        event.preventDefault();
        handleReset();
        return;
      }
      if (event.key === ">") {
        event.preventDefault();
        handlePortal();
        return;
      }
      const direction = KEY_TO_DIRECTION[event.key];
      if (direction) {
        event.preventDefault();
        handleMove(direction);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [screen, handleMove, handlePortal, handleReset]);

  if (screen === "start") {
    return <StartScreen onStart={startGame} loading={loading} error={error} />;
  }

  return (
    <div className="app game-screen">
      <div className="game-shell">
        <header className="title-bar">
          <h1>Treasure Runner</h1>
          <span className="player-tag">{state?.player_name}</span>
        </header>

        <HUD state={state} error={error} />

        <div className="play-area">
          <GameBoard state={state} onMove={handleMove} disabled={loading || state?.victory} />
          <aside className="side-panel">
            <Minimap state={state} />
            <div className="legend">
              <h3>Legend</h3>
              <ul>
                <li><span className="chip wall" /> Wall</li>
                <li><span className="chip floor" /> Floor</li>
                <li><span className="chip player" /> You</li>
                <li><span className="chip treasure" /> Treasure</li>
                <li><span className="chip portal" /> Portal</li>
              </ul>
            </div>
            <div className="controls-help">
              <h3>Controls</h3>
              <p>WASD / arrows — move</p>
              <p>&gt; — use portal</p>
              <p>R — reset</p>
            </div>
            <TouchControls
              onMove={handleMove}
              onPortal={handlePortal}
              disabled={loading || state?.victory}
            />
            <button
              type="button"
              className="btn secondary"
              onClick={handleReset}
              disabled={loading}
            >
              Reset Game
            </button>
          </aside>
        </div>
      </div>

      {state?.victory && (
        <VictoryModal
          state={state}
          onPlayAgain={handleReset}
        />
      )}
    </div>
  );
}
