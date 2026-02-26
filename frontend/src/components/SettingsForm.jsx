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

export default function SettingsForm({ settings, onSave }) {
  const [form, setForm] = useState({
    origin: "",
    destination: "",
    active: false,
    mode: "travel_time",
    alert_threshold_minutes: "",
    arrive_by: "",
    buffer_minutes: "",
  });

  useEffect(() => {
    if (settings) {
      setForm({
        origin: settings.origin || "",
        destination: settings.destination || "",
        active: settings.active || false,
        mode: settings.mode || "travel_time",
        alert_threshold_minutes: settings.alert_threshold_minutes ?? "",
        arrive_by: toLocalDatetime(settings.arrive_by),
        buffer_minutes: settings.buffer_minutes ?? "",
      });
    }
  }, [settings]);

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

  return (
    <form onSubmit={handleSubmit}>
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

      <button type="submit">Save Settings</button>
    </form>
  );
}
