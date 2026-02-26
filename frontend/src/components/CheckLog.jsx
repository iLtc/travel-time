const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "0.9rem",
};

const thStyle = {
  textAlign: "left",
  borderBottom: "2px solid #ccc",
  padding: "0.4rem 0.6rem",
};

const tdStyle = {
  borderBottom: "1px solid #eee",
  padding: "0.4rem 0.6rem",
};

function formatTime(unix) {
  return new Date(unix * 1000).toLocaleString();
}

export default function CheckLog({ checks, onClear }) {
  if (!checks.length) return <p>No checks yet.</p>;

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
        <h2 style={{ fontSize: "1.1rem", margin: 0 }}>Recent Checks</h2>
        <button onClick={onClear} style={{ fontSize: "0.8rem" }}>Clear Logs</button>
      </div>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Time</th>
            <th style={thStyle}>Travel (min)</th>
            <th style={thStyle}>Alerted</th>
          </tr>
        </thead>
        <tbody>
          {checks.map((c) => (
            <tr key={c.id}>
              <td style={tdStyle}>{formatTime(c.checked_at)}</td>
              <td style={tdStyle}>{Math.round(c.travel_minutes)}</td>
              <td style={tdStyle}>{c.alerted ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
