export default function VictoryModal({ state, onPlayAgain }) {
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <p className="eyebrow">Victory</p>
        <h2>You found all the treasure!</h2>
        <p>
          {state.player_name} collected {state.treasures_collected} treasures in{" "}
          {state.steps} steps.
        </p>
        <button type="button" className="btn primary" onClick={onPlayAgain}>
          Play Again
        </button>
      </div>
    </div>
  );
}
