import { useState, useEffect, useCallback } from "react";
import SettingsForm from "./components/SettingsForm";
import CheckLog from "./components/CheckLog";

const styles = {
  container: {
    maxWidth: 600,
    margin: "0 auto",
    padding: "2rem 1rem",
    fontFamily: "system-ui, -apple-system, sans-serif",
  },
  h1: {
    fontSize: "1.5rem",
    marginBottom: "1.5rem",
  },
};

export default function App() {
  const [settings, setSettings] = useState(null);
  const [checks, setChecks] = useState([]);
  const [triggering, setTriggering] = useState(false);

  const fetchSettings = useCallback(async () => {
    const res = await fetch("/api/settings");
    setSettings(await res.json());
  }, []);

  const fetchChecks = useCallback(async () => {
    const res = await fetch("/api/checks?limit=20");
    setChecks(await res.json());
  }, []);

  useEffect(() => {
    fetchSettings();
    fetchChecks();
    const id = setInterval(fetchChecks, 30_000);
    return () => clearInterval(id);
  }, [fetchSettings, fetchChecks]);

  const handleSave = async (data) => {
    const res = await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    setSettings(await res.json());
  };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      await fetch("/api/checks/trigger", { method: "POST" });
      await fetchChecks();
    } finally {
      setTriggering(false);
    }
  };

  const handleClear = async () => {
    await fetch("/api/checks", { method: "DELETE" });
    setChecks([]);
  };

  if (!settings) return <p>Loading…</p>;

  return (
    <div style={styles.container}>
      <h1 style={styles.h1}>Travel Time Alerter</h1>
      <SettingsForm settings={settings} onSave={handleSave} />
      <hr style={{ margin: "1.5rem 0" }} />
      <button onClick={handleTrigger} disabled={triggering} style={{ marginBottom: "1rem" }}>
        {triggering ? "Checking…" : "Check Now"}
      </button>
      <CheckLog checks={checks} onClear={handleClear} />
    </div>
  );
}
