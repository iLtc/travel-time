import { useState, useEffect } from "react";

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

function toLocalDatetime(unix) {
  if (!unix) return "";
  const d = new Date(unix * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalDatetime(str) {
  if (!str) return null;
  return Math.floor(new Date(str).getTime() / 1000);
}

export default function MonitorForm({ monitor, onSave, onDelete }) {
  const [form, setForm] = useState({
    name: "",
    origin: "",
    destination: "",
    active: false,
    mode: "arrive_time",
    alert_threshold_minutes: "",
    arrive_by: "",
    buffer_minutes: "",
  });

  useEffect(() => {
    if (monitor) {
      setForm({
        name: monitor.name || "",
        origin: monitor.origin || "",
        destination: monitor.destination || "",
        active: monitor.active || false,
        mode: monitor.mode || "travel_time",
        alert_threshold_minutes: monitor.alert_threshold_minutes ?? "",
        arrive_by: toLocalDatetime(monitor.arrive_by),
        buffer_minutes: monitor.buffer_minutes ?? "",
      });
    }
  }, [monitor]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      name: form.name,
      origin: form.origin,
      destination: form.destination,
      active: form.active,
      mode: form.mode,
    };

    if (form.mode === "travel_time") {
      data.alert_threshold_minutes = form.alert_threshold_minutes
        ? Number(form.alert_threshold_minutes)
        : null;
    } else {
      data.arrive_by = fromLocalDatetime(form.arrive_by);
      data.buffer_minutes = form.buffer_minutes
        ? Number(form.buffer_minutes)
        : null;
    }

    onSave(data);
  };

  const handleDelete = () => {
    if (confirm("Delete this monitor and all its logs?")) {
      onDelete();
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={fieldStyle}>
        <label>Name (optional)</label>
        <input style={inputStyle} name="name" value={form.name} onChange={handleChange} placeholder="e.g. Morning commute" />
      </div>

      <div style={fieldStyle}>
        <label>Origin</label>
        <input style={inputStyle} name="origin" value={form.origin} onChange={handleChange} placeholder="e.g. Edinburgh Waverley Station" />
      </div>

      <div style={fieldStyle}>
        <label>Destination</label>
        <input style={inputStyle} name="destination" value={form.destination} onChange={handleChange} placeholder="e.g. Glasgow Queen Street" />
      </div>

      <div style={fieldStyle}>
        <label>Mode</label>
        <select style={inputStyle} name="mode" value={form.mode} onChange={handleChange}>
          <option value="travel_time">Travel Time (alert when under threshold)</option>
          <option value="arrive_time">Arrive Time (alert when you need to leave)</option>
        </select>
      </div>

      {form.mode === "travel_time" && (
        <div style={fieldStyle}>
          <label>Alert threshold (minutes)</label>
          <input style={inputStyle} name="alert_threshold_minutes" type="number" min="1" value={form.alert_threshold_minutes} onChange={handleChange} placeholder="e.g. 45" />
        </div>
      )}

      {form.mode === "arrive_time" && (
        <>
          <div style={fieldStyle}>
            <label>Arrive by</label>
            <input style={inputStyle} name="arrive_by" type="datetime-local" value={form.arrive_by} onChange={handleChange} />
          </div>
          <div style={fieldStyle}>
            <label>Buffer (minutes)</label>
            <input style={inputStyle} name="buffer_minutes" type="number" min="0" value={form.buffer_minutes} onChange={handleChange} placeholder="e.g. 15" />
          </div>
        </>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "1rem" }}>
        <input type="checkbox" name="active" checked={form.active} onChange={handleChange} id="active" />
        <label htmlFor="active">Monitoring active</label>
      </div>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button type="submit">Save</button>
        <button type="button" onClick={handleDelete} style={{ color: "#c00" }}>Delete Monitor</button>
      </div>
    </form>
  );
}
