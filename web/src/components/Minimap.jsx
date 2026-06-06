export default function Minimap({ state }) {
  if (!state?.room_ids?.length) return null;

  const visited = new Set(state.visited_rooms);
  const current = state.room_id;

  return (
    <div className="minimap">
      <h3>World Map</h3>
      <div className="minimap-grid">
        {state.room_ids.map((id) => {
          let cls = "room-node unvisited";
          if (id === current) cls = "room-node current";
          else if (visited.has(id)) cls = "room-node visited";
          return (
            <div key={id} className={cls} title={`Room ${id + 1}`}>
              {id + 1}
            </div>
          );
        })}
      </div>
    </div>
  );
}
