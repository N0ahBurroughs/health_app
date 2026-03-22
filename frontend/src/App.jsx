import { useEffect, useMemo, useState } from "react";

const defaultMetrics = {
  heart_rate: 72,
  hrv: 52,
  sleep_hours: 7.4,
  resting_heart_rate: 58
};

const taskOptions = [
  { value: "daily_check", label: "Daily Check" },
  { value: "training_reco", label: "Training Recommendation" },
  { value: "anomaly_alert", label: "Anomaly Alert" }
];

export default function App() {
  const apiBase = useMemo(
    () => import.meta.env.VITE_API_BASE || "http://localhost:8000",
    []
  );

  const [userId, setUserId] = useState("noah");
  const [taskType, setTaskType] = useState("daily_check");
  const [metrics, setMetrics] = useState(defaultMetrics);
  const [agentResult, setAgentResult] = useState(null);
  const [toolList, setToolList] = useState([]);
  const [toolName, setToolName] = useState("");
  const [toolArgs, setToolArgs] = useState("{\n  \"user_id\": \"noah\",\n  \"days\": 7\n}");
  const [toolResult, setToolResult] = useState(null);
  const [runs, setRuns] = useState([]);
  const [memory, setMemory] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    fetch(`${apiBase}/mcp/tools`)
      .then((res) => res.json())
      .then((data) => {
        const tools = Object.keys(data.tools || {});
        setToolList(tools);
        if (tools.length && !toolName) setToolName(tools[0]);
      })
      .catch(() => setToolList([]));
  }, [apiBase, toolName]);

  const fetchRuns = () => {
    fetch(`${apiBase}/api/agent-runs?user_id=${encodeURIComponent(userId)}`)
      .then((res) => res.json())
      .then(setRuns)
      .catch(() => setRuns([]));
  };

  const fetchMemory = () => {
    fetch(`${apiBase}/api/memory?user_id=${encodeURIComponent(userId)}`)
      .then((res) => res.json())
      .then(setMemory)
      .catch(() => setMemory([]));
  };

  const runAgent = () => {
    setStatus("Running agents...");
    setAgentResult(null);
    fetch(`${apiBase}/api/agent/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_type: taskType,
        input: {
          user_id: userId,
          timestamp: new Date().toISOString(),
          metrics
        }
      })
    })
      .then((res) => res.json())
      .then((data) => {
        setAgentResult(data);
        setStatus("Run complete");
        fetchRuns();
        fetchMemory();
      })
      .catch(() => setStatus("Failed to run agents"));
  };

  const callTool = () => {
    setStatus("Calling tool...");
    let parsed = {};
    try {
      parsed = JSON.parse(toolArgs);
    } catch (err) {
      setStatus("Invalid JSON for tool arguments");
      return;
    }
    fetch(`${apiBase}/mcp/tool/call`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tool: toolName,
        arguments: parsed
      })
    })
      .then((res) => res.json())
      .then((data) => {
        setToolResult(data);
        setStatus("Tool call complete");
      })
      .catch(() => setStatus("Tool call failed"));
  };

  return (
    <div className="app">
      <header>
        <div className="badge">Health Agent Ops</div>
        <h1>Multi-Agent Health Command Center</h1>
        <p>
          Run orchestration flows, call MCP tools, and inspect memory in one place.
        </p>
      </header>

      <section className="grid">
        <div className="card">
          <h2>Run Agents</h2>
          <label>User ID</label>
          <input value={userId} onChange={(e) => setUserId(e.target.value)} />

          <label>Task Type</label>
          <select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
            {taskOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <div className="metrics">
            {Object.keys(metrics).map((key) => (
              <div key={key}>
                <label>{key.replace("_", " ")}</label>
                <input
                  type="number"
                  value={metrics[key]}
                  onChange={(e) =>
                    setMetrics((prev) => ({ ...prev, [key]: Number(e.target.value) }))
                  }
                />
              </div>
            ))}
          </div>

          <button onClick={runAgent}>Run Orchestration</button>
          {status && <p className="status">{status}</p>}
          {agentResult && (
            <pre className="output">{JSON.stringify(agentResult, null, 2)}</pre>
          )}
        </div>

        <div className="card">
          <h2>MCP Tools</h2>
          <label>Tool</label>
          <select value={toolName} onChange={(e) => setToolName(e.target.value)}>
            {toolList.map((tool) => (
              <option key={tool} value={tool}>
                {tool}
              </option>
            ))}
          </select>
          <label>Arguments (JSON)</label>
          <textarea value={toolArgs} onChange={(e) => setToolArgs(e.target.value)} />
          <button onClick={callTool}>Call Tool</button>
          {toolResult && <pre className="output">{JSON.stringify(toolResult, null, 2)}</pre>}
        </div>

        <div className="card">
          <h2>Agent Traces</h2>
          <p className="muted">Latest agent runs for this user.</p>
          <button onClick={fetchRuns}>Refresh Runs</button>
          <div className="scroll">
            {runs.map((run) => (
              <div key={`${run.run_id}-${run.agent_name}`} className="trace">
                <div className="trace-header">
                  <span>{run.agent_name}</span>
                  <span>{new Date(run.created_at).toLocaleString()}</span>
                </div>
                <div className="trace-body">
                  <strong>Latency:</strong> {run.latency_ms}ms
                  <pre>{JSON.stringify(run.output, null, 2)}</pre>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2>Memory Store</h2>
          <p className="muted">Long-term memory chunks for this user.</p>
          <button onClick={fetchMemory}>Refresh Memory</button>
          <div className="scroll">
            {memory.map((item) => (
              <div key={item.id} className="memory">
                <div className="trace-header">
                  <span>{item.type}</span>
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                </div>
                <p>{item.content}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
