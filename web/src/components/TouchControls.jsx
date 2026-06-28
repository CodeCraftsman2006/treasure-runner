export default function TouchControls({ onMove, onPortal, disabled }) {
  return (
    <div className="touch-controls">
      <h3>Touch Controls</h3>
      <div className="dpad">
        <button type="button" className="btn dpad-btn" disabled={disabled} onClick={() => onMove("north")}>↑</button>
        <div className="dpad-row">
          <button type="button" className="btn dpad-btn" disabled={disabled} onClick={() => onMove("west")}>←</button>
          <button type="button" className="btn dpad-btn portal-btn" disabled={disabled} onClick={onPortal}>&gt;</button>
          <button type="button" className="btn dpad-btn" disabled={disabled} onClick={() => onMove("east")}>→</button>
        </div>
        <button type="button" className="btn dpad-btn" disabled={disabled} onClick={() => onMove("south")}>↓</button>
      </div>
    </div>
  );
}
