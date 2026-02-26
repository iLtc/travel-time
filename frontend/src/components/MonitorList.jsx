const listStyle = {
  listStyle: "none",
  padding: 0,
  margin: "0 0 1rem 0",
};

const itemStyle = (selected) => ({
  padding: "0.5rem 0.75rem",
  marginBottom: "0.25rem",
  border: "1px solid",
  borderColor: selected ? "#333" : "#ccc",
  borderRadius: 4,
  cursor: "pointer",
  background: selected ? "#f0f0f0" : "white",
  fontWeight: selected ? "bold" : "normal",
});

function monitorLabel(monitor) {
  if (monitor.name) return monitor.name;
  if (monitor.origin && monitor.destination) return `${monitor.origin} → ${monitor.destination}`;
  return `Monitor #${monitor.id}`;
}

export default function MonitorList({ monitors, selectedId, onSelect, onAdd }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
        <h2 style={{ fontSize: "1.1rem", margin: 0 }}>Monitors</h2>
        <button onClick={onAdd} style={{ fontSize: "0.85rem" }}>+ Add Monitor</button>
      </div>
      {monitors.length === 0 && <p style={{ color: "#888", fontSize: "0.9rem" }}>No monitors yet. Add one to get started.</p>}
      <ul style={listStyle}>
        {monitors.map((m) => (
          <li key={m.id} style={itemStyle(m.id === selectedId)} onClick={() => onSelect(m.id)}>
            {monitorLabel(m)}
            {m.active && <span style={{ marginLeft: 8, fontSize: "0.75rem", color: "#080" }}>active</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
