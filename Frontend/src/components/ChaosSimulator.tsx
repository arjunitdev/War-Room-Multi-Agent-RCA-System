import { useState, useEffect } from 'react';

interface Scenario {
  name: string;
  description: string;
  payloads: Payload[];
}

interface Payload {
  source: 'NETWORK' | 'DATABASE' | 'CODE';
  alert_name: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  delay: number;
  logs: string;
}

const API_BASE = '/api';

export function ChaosSimulator() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<Array<{ time: string; message: string }>>(() => {
    // Restore logs from localStorage on mount
    const savedLogs = localStorage.getItem('chaos_simulator_logs');
    return savedLogs ? JSON.parse(savedLogs) : [];
  });
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadScenarios();
  }, []);

  // Persist logs to localStorage whenever they change
  useEffect(() => {
    if (logs.length > 0) {
      localStorage.setItem('chaos_simulator_logs', JSON.stringify(logs));
    }
  }, [logs]);

  const loadScenarios = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/scenarios`);
      if (!response.ok) throw new Error('Failed to load scenarios');
      
      const data = await response.json();
      setScenarios(data.scenarios);
      if (data.scenarios.length > 0) {
        setSelectedScenario(data.scenarios[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  };

  const executeScenario = async () => {
    if (!selectedScenario) return;
    
    setIsRunning(true);
    setLogs([]);
    setProgress(0);
    localStorage.removeItem('chaos_simulator_logs');

    try {
      addLog(`Starting scenario: ${selectedScenario.name}`);
      
      const response = await fetch(`${API_BASE}/scenarios/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario_name: selectedScenario.name
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to execute scenario: ${response.statusText}`);
      }

      const result = await response.json();
      addLog(`Scenario started: ${result.total_payloads} payloads queued`);

      // The backend handles the actual payload sending with proper delays
      // Just show progress feedback in the UI
      addLog(`Executing scenario in background...`);
      setProgress(100);

      addLog(`Scenario execution complete`);
    } catch (err) {
      addLog(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsRunning(false);
    }
  };

  const addLog = (message: string) => {
    const time = new Date().toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
    setLogs(prev => [{ time, message }, ...prev]);
  };

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const clearAll = async () => {
    try {
      const response = await fetch(`${API_BASE}/incidents/clear`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to clear incidents');
      }
      
      const result = await response.json();
      setLogs([]);
      setProgress(0);
      localStorage.removeItem('chaos_simulator_logs');
      addLog(`All incidents cleared (${result.count} incidents)`);
    } catch (err) {
      addLog(`Error clearing incidents: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl">
        <div className="flex items-center justify-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-black/20 border-t-black rounded-full animate-spin" />
          <span className="ml-3 text-black/60">Loading scenarios...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <h3 className="text-red-900 mb-2">Error loading scenarios</h3>
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={loadScenarios}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!selectedScenario) {
    return (
      <div className="max-w-4xl">
        <div className="text-center py-12">
          <p className="text-black/60">No scenarios available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl">
      <div className="space-y-8">
        {/* Hero */}
        <div>
          <h2 className="text-3xl mb-3">Chaos Simulator</h2>
          <p className="text-black/60 leading-relaxed">
            Test system resilience by simulating multi-domain failure scenarios.
            Each scenario triggers sequential alerts across network, database, and application layers.
          </p>
        </div>

        {/* Scenario Selection */}
        <div className="space-y-3">
          <label className="block text-sm text-black/70">
            Select Scenario
          </label>
          <select
            value={selectedScenario.name}
            onChange={(e) => {
              const scenario = scenarios.find(s => s.name === e.target.value);
              if (scenario) setSelectedScenario(scenario);
            }}
            disabled={isRunning}
            className="w-full px-4 py-3 bg-white border border-black/20 rounded-lg text-sm focus:outline-none focus:border-black disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {scenarios.map(scenario => (
              <option key={scenario.name} value={scenario.name}>
                {scenario.name}
              </option>
            ))}
          </select>
          <p className="text-xs text-black/50">
            {selectedScenario.description}
          </p>
        </div>

        {/* Scenario Preview */}
        <div className="bg-white border border-black/10 rounded-xl p-6">
          <h3 className="text-lg mb-3">{selectedScenario.name}</h3>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-blue-900 font-medium">Scenario: {selectedScenario.name}</p>
            <p className="text-blue-700 text-sm mt-1">
              Payloads: {selectedScenario.payloads.length} sequential alerts
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-black/50 hover:text-black transition-colors"
            >
              {showDetails ? 'Hide Payload Details' : 'View Payload Details'}
            </button>

            {showDetails && (
              <div className="space-y-4 pt-4 border-t border-black/10">
                {selectedScenario.payloads.map((payload, idx) => (
                  <div key={idx} className="space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-black/70">
                        Payload {idx + 1}: {payload.source} ({payload.severity})
                      </span>
                    </div>
                    <p className="text-sm font-medium text-black/80">Alert: {payload.alert_name}</p>
                    <p className="text-xs text-black/50">Delay: {payload.delay}s</p>
                    <div className="bg-black/5 p-3 rounded">
                      <p className="text-xs font-medium text-black/60 mb-2">Logs:</p>
                      <pre className="text-xs text-black/70 whitespace-pre-wrap font-mono">
{payload.logs}
                      </pre>
                    </div>
                    {idx < selectedScenario.payloads.length - 1 && (
                      <div className="h-px bg-black/10 my-4" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={executeScenario}
            disabled={isRunning}
            className="flex-1 px-6 py-3 bg-black text-white rounded-full hover:bg-black/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
          >
            {isRunning ? 'Running scenario...' : 'Execute scenario'}
          </button>
          <button
            onClick={clearAll}
            disabled={isRunning}
            className="px-6 py-3 border border-black/20 rounded-full hover:bg-black/5 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
          >
            Clear all
          </button>
        </div>

        {/* Progress */}
        {isRunning && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-black/60">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-1 bg-black/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-black transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Event Log */}
        {logs.length > 0 && (
          <div className="bg-white border border-black/10 rounded-xl p-6">
            <h3 className="text-sm text-black/50 mb-4">Event Log</h3>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {logs.map((log, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 text-sm font-mono p-2 hover:bg-black/5 rounded transition-colors"
                >
                  <span className="text-black/40">{log.time}</span>
                  <span className="text-black/70">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info */}
        <div className="bg-[#e8e6e1] rounded-xl p-6">
          <p className="text-sm text-black/70 leading-relaxed">
            Each scenario simulates a realistic production incident by sending sequential alerts
            with configurable delays. Monitor the War Room tab to observe real-time incident
            detection and multi-agent root cause analysis.
          </p>
        </div>
      </div>
    </div>
  );
}
