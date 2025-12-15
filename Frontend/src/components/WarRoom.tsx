import { useState, useEffect } from 'react';

const API_BASE = '/api';

interface Incident {
  id: string;
  alert_name: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  category: 'Network' | 'Database' | 'Code';
  received_at: string;
  logs: Record<string, string>;
}

interface AgentAnalysis {
  agent_name: string;
  status: 'Critical' | 'Warning' | 'Healthy';
  hypothesis: string;
  confidence: number;
  evidence: string[];
  reasoning: string;
  timestamp: string;
}

interface CategoryStatus {
  category: string;
  count: number;
  incidents: Incident[];
}

export function WarRoom() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [lastCheck, setLastCheck] = useState<Date>(new Date());
  const [agentAnalyses, setAgentAnalyses] = useState<AgentAnalysis[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [judgeVerdict, setJudgeVerdict] = useState<{
    rootCause: string;
    explanation: string;
    remediation: string;
  } | null>(null);
  const [showAgentDetails, setShowAgentDetails] = useState<Record<string, boolean>>({});
  const [apiKey, setApiKey] = useState<string>('');
  const [apiKeyConfigured, setApiKeyConfigured] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if API key is configured in environment
    checkApiKeyConfig();
    
    // Load API key from localStorage
    const savedApiKey = localStorage.getItem('war-room-api-key');
    if (savedApiKey) {
      setApiKey(savedApiKey);
    }

    // Start polling for incidents
    loadIncidents();
    const interval = setInterval(loadIncidents, 2000);
    return () => clearInterval(interval);
  }, []);

  const checkApiKeyConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/config`);
      if (response.ok) {
        const config = await response.json();
        setApiKeyConfigured(config.api_key_configured);
      }
    } catch (err) {
      console.warn('Failed to check API key configuration:', err);
    }
  };

  const loadIncidents = async () => {
    try {
      const response = await fetch(`${API_BASE}/incidents/status`);
      if (!response.ok) throw new Error('Failed to load incidents');
      
      const data = await response.json();
      
      // Convert incidents_by_category to flat array
      const allIncidents: Incident[] = [];
      Object.entries(data.incidents_by_category).forEach(([category, categoryIncidents]) => {
        (categoryIncidents as Incident[]).forEach(incident => {
          allIncidents.push({
            ...incident,
            category: category as 'Network' | 'Database' | 'Code'
          });
        });
      });
      
      setIncidents(allIncidents);
      setLastCheck(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load incidents');
    } finally {
      setLoading(false);
    }
  };

  const categoryStatuses: CategoryStatus[] = [
    {
      category: 'Network',
      count: incidents.filter(i => i.category === 'Network').length,
      incidents: incidents.filter(i => i.category === 'Network')
    },
    {
      category: 'Database',
      count: incidents.filter(i => i.category === 'Database').length,
      incidents: incidents.filter(i => i.category === 'Database')
    },
    {
      category: 'Code',
      count: incidents.filter(i => i.category === 'Code').length,
      incidents: incidents.filter(i => i.category === 'Code')
    }
  ];

  const hasActiveIncidents = incidents.length > 0;
  const totalIncidents = incidents.length;

  const handleCheckNow = () => {
    loadIncidents();
  };

  const saveApiKey = (key: string) => {
    setApiKey(key);
    localStorage.setItem('war-room-api-key', key);
  };

  const handleTroubleshoot = async () => {
    if (!apiKeyConfigured && !apiKey) {
      setError('API key is required for troubleshooting');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/troubleshoot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: apiKeyConfigured ? null : apiKey, // Don't send API key if it's in environment
          force_all_agents: !hasActiveIncidents
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Troubleshooting failed');
      }

      const result = await response.json();
      
      // Convert API response to component format
      const analyses: AgentAnalysis[] = result.agent_results.map((agent: any) => ({
        agent_name: agent.agent_name,
        status: agent.status,
        hypothesis: agent.hypothesis,
        confidence: agent.confidence_score,
        evidence: agent.evidence_cited,
        reasoning: agent.reasoning,
        timestamp: agent.timestamp
      }));
      
      setAgentAnalyses(analyses);
      
      if (result.judge_verdict) {
        setJudgeVerdict({
          rootCause: result.judge_verdict.root_cause_headline,
          explanation: result.judge_verdict.scenarios_logic,
          remediation: result.judge_verdict.remediation_plan
        });
      } else if (result.judge_error) {
        setError(`Judge Analysis Failed: ${result.judge_error}`);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Troubleshooting failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleAgentDetails = (agentName: string) => {
    setShowAgentDetails(prev => ({
      ...prev,
      [agentName]: !prev[agentName]
    }));
  };

  return (
    <div className="max-w-6xl">
      <div className="space-y-8">
        {/* Hero */}
        <div>
          <h2 className="text-3xl mb-3">War Room</h2>
          <p className="text-black/60 leading-relaxed">
            Real-time incident monitoring and multi-agent root cause analysis.
            Independent specialist agents analyze domain-specific evidence to determine failure origins.
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Status Bar */}
        <div className="bg-white border border-black/10 rounded-xl p-6">
          <div className="grid grid-cols-3 gap-6">
            <div>
              <p className="text-xs text-black/50 mb-2">System Status</p>
              <p className="text-sm">
                {hasActiveIncidents 
                  ? `${totalIncidents} active incident${totalIncidents > 1 ? 's' : ''}`
                  : 'All systems operational'
                }
              </p>
            </div>
            <div>
              <p className="text-xs text-black/50 mb-2">Last Check</p>
              <p className="text-sm font-mono">
                {lastCheck.toLocaleTimeString('en-US', { hour12: false })}
              </p>
              <p className="text-xs text-black/40 mt-1">Polling: 2s interval</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCheckNow}
                className="flex-1 px-4 py-2 border border-black/20 rounded-lg hover:bg-black/5 transition-colors text-sm"
              >
                Refresh now
              </button>
              <button
                onClick={handleTroubleshoot}
                disabled={isAnalyzing || (!apiKeyConfigured && !apiKey)}
                className="flex-1 px-4 py-2 bg-black text-white rounded-lg hover:bg-black/90 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-sm"
              >
                {isAnalyzing ? 'Analyzing...' : 'Troubleshoot'}
              </button>
            </div>
          </div>
        </div>

        {/* Category Status */}
        <div>
          <h3 className="text-sm text-black/50 mb-4">Status by Category</h3>
          <div className="grid grid-cols-3 gap-4">
            {categoryStatuses.map((status) => (
              <div
                key={status.category}
                className={`rounded-xl p-6 border-2 transition-colors ${
                  status.count > 0
                    ? 'border-red-600 bg-red-50'
                    : 'border-green-600 bg-green-50'
                }`}
              >
                <h4 className={`text-lg mb-3 ${
                  status.count > 0 ? 'text-red-900' : 'text-green-900'
                }`}>
                  {status.category}
                </h4>
                <p className={`text-2xl mb-2 ${
                  status.count > 0 ? 'text-red-700' : 'text-green-700'
                }`}>
                  {status.count > 0 ? `${status.count} active` : 'Healthy'}
                </p>
                
                {status.incidents.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {status.incidents.map((incident) => (
                      <div
                        key={incident.id}
                        className="bg-white/70 rounded-lg p-3 border-l-2 border-red-700"
                      >
                        <p className="text-xs text-red-900 mb-1">{incident.alert_name}</p>
                        <p className="text-xs text-black/50">
                          {incident.severity} • {new Date(incident.received_at).toLocaleTimeString('en-US', { hour12: false })}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* No Incidents Message */}
        {!hasActiveIncidents && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
            <h3 className="text-lg mb-2">All Systems Operational</h3>
            <p className="text-sm text-black/60">
              No active incidents detected. Use the Chaos Simulator to test incident response.
            </p>
          </div>
        )}

        {/* Active Incidents Alert */}
        {hasActiveIncidents && !agentAnalyses.length && !isAnalyzing && (
          <div className="bg-yellow-50 border border-yellow-300 rounded-xl p-6">
            <h3 className="text-lg mb-2">Active Incidents Detected</h3>
            <p className="text-sm text-black/70">
              Click "Troubleshoot" to initiate multi-agent root cause analysis.
            </p>
          </div>
        )}

        {/* Analysis in Progress */}
        {isAnalyzing && (
          <div className="bg-white border border-black/10 rounded-xl p-8 text-center">
            <div className="inline-block w-8 h-8 border-2 border-black/20 border-t-black rounded-full animate-spin mb-4" />
            <p className="text-sm text-black/60">
              Running analysis across {categoryStatuses.filter(s => s.count > 0).length} domain specialist{categoryStatuses.filter(s => s.count > 0).length > 1 ? 's' : ''}
            </p>
          </div>
        )}

        {/* Agent Analysis Results */}
        {agentAnalyses.length > 0 && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg mb-2">Agent Analysis</h3>
              <p className="text-sm text-black/60">
                Independent specialist analysis from domain experts
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {agentAnalyses.map((analysis) => (
                <div
                  key={analysis.agent_name}
                  className="bg-white border border-black/10 rounded-xl p-6 space-y-4"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-black/50 mb-1">Agent</p>
                      <p className="text-base">{analysis.agent_name}</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs ${
                      analysis.status === 'Critical'
                        ? 'bg-red-100 text-red-900'
                        : analysis.status === 'Warning'
                        ? 'bg-yellow-100 text-yellow-900'
                        : 'bg-green-100 text-green-900'
                    }`}>
                      {analysis.status}
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-black/50 mb-1">Hypothesis</p>
                    <p className="text-sm text-black/80">{analysis.hypothesis}</p>
                  </div>

                  <div>
                    <p className="text-xs text-black/50 mb-1">Confidence</p>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-1 bg-black/10 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-black"
                          style={{ width: `${analysis.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-mono">{(analysis.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  <button
                    onClick={() => toggleAgentDetails(analysis.agent_name)}
                    className="text-xs text-black/50 hover:text-black transition-colors"
                  >
                    {showAgentDetails[analysis.agent_name] ? 'Hide details' : 'View details'}
                  </button>

                  {showAgentDetails[analysis.agent_name] && (
                    <div className="space-y-3 pt-3 border-t border-black/10">
                      <div>
                        <p className="text-xs text-black/50 mb-2">Evidence</p>
                        <ul className="space-y-1">
                          {analysis.evidence.map((item, idx) => (
                            <li key={idx} className="text-xs text-black/70 pl-3 relative before:content-['•'] before:absolute before:left-0">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-xs text-black/50 mb-2">Reasoning</p>
                        <p className="text-xs text-black/70 leading-relaxed">
                          {analysis.reasoning}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Judge Verdict */}
        {judgeVerdict && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg mb-2">Final Verdict</h3>
              <p className="text-sm text-black/60">
                Synthesized analysis from all domain specialists
              </p>
            </div>

            <div className="bg-white border border-black/10 rounded-xl p-8 space-y-6">
              <div>
                <p className="text-xs text-black/50 mb-2">Root Cause</p>
                <p className="text-xl">{judgeVerdict.rootCause}</p>
              </div>

              <div>
                <p className="text-xs text-black/50 mb-2">Analysis</p>
                <p className="text-sm text-black/70 leading-relaxed whitespace-pre-line">
                  {judgeVerdict.explanation}
                </p>
              </div>

              <div>
                <p className="text-xs text-black/50 mb-2">Remediation Plan</p>
                <p className="text-sm text-black/70 leading-relaxed whitespace-pre-line">
                  {judgeVerdict.remediation}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
