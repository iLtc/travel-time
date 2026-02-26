import { useState, useEffect, useCallback } from "react";
import MonitorList from "./components/MonitorList";
import MonitorForm from "./components/MonitorForm";
import CheckLog from "./components/CheckLog";

const styles = {
  container: {
    maxWidth: 680,
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
  const [monitors, setMonitors] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [checks, setChecks] = useState([]);
  const [triggering, setTriggering] = useState(false);

  const fetchMonitors = useCallback(async () => {
    const res = await fetch("/api/monitors");
    setMonitors(await res.json());
  }, []);

  const fetchChecks = useCallback(async (id) => {
    if (!id) { setChecks([]); return; }
    const res = await fetch(`/api/monitors/${id}/checks?limit=20`);
    setChecks(await res.json());
  }, []);

  useEffect(() => {
    fetchMonitors();
  }, [fetchMonitors]);

  useEffect(() => {
    fetchChecks(selectedId);
    const interval = setInterval(() => fetchChecks(selectedId), 30_000);
    return () => clearInterval(interval);
  }, [selectedId, fetchChecks]);

  const handleAdd = async () => {
    const res = await fetch("/api/monitors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const created = await res.json();
    setMonitors((prev) => [...prev, created]);
    setSelectedId(created.id);
  };

  const handleSave = async (data) => {
    const res = await fetch(`/api/monitors/${selectedId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const updated = await res.json();
    setMonitors((prev) => prev.map((m) => (m.id === selectedId ? updated : m)));
  };

  const handleDelete = async () => {
    await fetch(`/api/monitors/${selectedId}`, { method: "DELETE" });
    setMonitors((prev) => prev.filter((m) => m.id !== selectedId));
    setSelectedId(null);
    setChecks([]);
  };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      await fetch(`/api/monitors/${selectedId}/checks/trigger`, { method: "POST" });
      await fetchChecks(selectedId);
    } finally {
      setTriggering(false);
    }
  };

  const handleClear = async () => {
    await fetch(`/api/monitors/${selectedId}/checks`, { method: "DELETE" });
    setChecks([]);
  };

  const selectedMonitor = monitors.find((m) => m.id === selectedId) ?? null;

  return (
    <div style={styles.container}>
      <h1 style={styles.h1}>Travel Time Alerter</h1>

      <MonitorList
        monitors={monitors}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onAdd={handleAdd}
      />

      {selectedMonitor && (
        <>
          <hr style={{ margin: "1.5rem 0" }} />
          <MonitorForm
            monitor={selectedMonitor}
            onSave={handleSave}
            onDelete={handleDelete}
          />
          <hr style={{ margin: "1.5rem 0" }} />
          <button onClick={handleTrigger} disabled={triggering} style={{ marginBottom: "1rem" }}>
            {triggering ? "Checking…" : "Check Now"}
          </button>
          <CheckLog checks={checks} onClear={handleClear} />
        </>
      )}
    </div>
  );
}
