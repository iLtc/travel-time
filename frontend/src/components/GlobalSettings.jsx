const fieldStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  marginBottom: "0.75rem",
};

const inputStyle = {
  padding: "0.4rem",
  fontSize: "1rem",
  border: "1px solid #ccc",
  borderRadius: 4,
};

export default function GlobalSettings({ settings, onSave }) {
  const checksEnabled = settings.checks_enabled !== "false";
  const defaultLocation = settings.default_location ?? "";

  const handleToggle = () => {
    onSave({ checks_enabled: checksEnabled ? "false" : "true" });
  };

  const handleLocationBlur = (e) => {
    const val = e.target.value;
    if (val !== defaultLocation) {
      onSave({ default_location: val });
    }
  };

  return (
    <div style={{ marginBottom: "1.5rem", padding: "0.75rem", border: "1px solid #ddd", borderRadius: 6 }}>
      <h2 style={{ fontSize: "1rem", marginTop: 0, marginBottom: "0.75rem" }}>Global Settings</h2>

      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "0.75rem" }}>
        <input
          type="checkbox"
          id="checks_enabled"
          checked={checksEnabled}
          onChange={handleToggle}
        />
        <label htmlFor="checks_enabled">Checks enabled</label>
        {!checksEnabled && <span style={{ fontSize: "0.8rem", color: "#c00" }}>All checks paused</span>}
      </div>

      <div style={fieldStyle}>
        <label>Default location (used when monitor origin is blank)</label>
        <input
          style={inputStyle}
          defaultValue={defaultLocation}
          onBlur={handleLocationBlur}
          placeholder="e.g. Edinburgh Waverley Station"
        />
      </div>
    </div>
  );
}
