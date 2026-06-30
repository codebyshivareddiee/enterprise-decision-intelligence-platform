import React, { useState, useEffect, useRef } from 'react';
import { HelpCircle, Paperclip, Lightbulb, ArrowRight, ShieldAlert, Check, Play, PlayCircle, Loader2, Maximize2, Plus, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { toast } from 'sonner';

export default function Decisions({ workspace, initialQuery, onDecisionComplete }) {
  const [subview, setSubview] = useState('input'); // 'input' | 'graph'
  const [queryText, setQueryText] = useState('');
  
  // Selection sources
  const [sources, setSources] = useState([
    { id: 'src-1', name: 'Vendor Profiles', active: true, color: 'active' },
    { id: 'src-2', name: 'Security Policies', active: true, color: 'active-blue' },
    { id: 'src-3', name: 'Business Rules', active: true, color: 'active-purple' }
  ]);

  // Dynamic execution state
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [nodeStates, setNodeStates] = useState({}); // { [stepId]: { status, startTime, endTime, stream, produced: [], consumed: [] } }
  const [timelineEvents, setTimelineEvents] = useState([]); // { timestamp, message, type }
  const [activeNodeId, setActiveNodeId] = useState(null);
  
  const [workflowState, setWorkflowState] = useState('pending'); // pending, running, completed, failed
  const [elapsedTime, setElapsedTime] = useState(0);
  const [decisionId, setDecisionId] = useState(null);

  const wsRef = useRef(null);
  const timerRef = useRef(null);

  const wsReconnectTimeout = useRef(null);
  const reconnectAttempt = useRef(0);

  useEffect(() => {
    if (initialQuery) {
      setQueryText(initialQuery);
    }
  }, [initialQuery]);
  
  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (wsReconnectTimeout.current) {
        clearTimeout(wsReconnectTimeout.current);
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Handle WebSocket connection
  const connectWebSocket = (id) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const wsBaseUrl = apiBaseUrl.replace(/^http/, 'ws');
    const wsUrl = `${wsBaseUrl}/decisions/ws/workflows/${id}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to workflow event stream:', id);
      reconnectAttempt.current = 0; // Reset on successful connect
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const timeStr = new Date(data.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      
      if (data.type === 'workflow_started') {
        setWorkflowState('running');
        addTimelineEvent(timeStr, 'Workflow Started', 'info');
      } else if (data.type === 'workflow_completed') {
        setWorkflowState('completed');
        addTimelineEvent(timeStr, 'Workflow Completed', 'success');
      } else if (data.type === 'workflow_failed') {
        setWorkflowState('failed');
        addTimelineEvent(timeStr, 'Workflow Failed', 'error');
      } else if (data.type === 'agent_started') {
        setNodeStates(prev => ({
          ...prev,
          [data.step_id]: { ...prev[data.step_id], status: 'running', startTime: data.timestamp }
        }));
        setActiveNodeId(data.step_id);
        addTimelineEvent(timeStr, `${data.agent_name} Running`, 'info');
      } else if (data.type === 'agent_completed') {
        setNodeStates(prev => ({
          ...prev,
          [data.step_id]: { 
            ...prev[data.step_id], 
            status: 'completed', 
            endTime: data.timestamp,
            duration: data.duration_ms,
            metrics: data.metrics || {}
          }
        }));
        addTimelineEvent(timeStr, `${data.agent_name} Completed`, 'success');
      } else if (data.type === 'agent_failed') {
        setNodeStates(prev => ({
          ...prev,
          [data.step_id]: { ...prev[data.step_id], status: 'failed', error: data.error }
        }));
        addTimelineEvent(timeStr, `${data.agent_name} Failed`, 'error');
      } else if (data.type === 'agent_skipped') {
        setNodeStates(prev => ({
          ...prev,
          [data.step_id]: { ...prev[data.step_id], status: 'skipped' }
        }));
        addTimelineEvent(timeStr, `Agent Skipped`, 'info');
      } else if (data.type === 'artifact_created') {
        setNodeStates(prev => {
          const current = prev[data.step_id] || { produced: [] };
          return {
            ...prev,
            [data.step_id]: { ...current, produced: [...(current.produced || []), data.artifact_name] }
          };
        });
      } else if (data.type === 'artifact_consumed') {
        setNodeStates(prev => {
          const current = prev[data.step_id] || { consumed: [] };
          return {
            ...prev,
            [data.step_id]: { ...current, consumed: [...(current.consumed || []), data.artifact_name] }
          };
        });
      } else if (data.type === 'agent_stream') {
        setNodeStates(prev => {
          const current = prev[data.step_id] || {};
          return {
            ...prev,
            [data.step_id]: { ...current, stream: (current.stream || '') + data.delta }
          };
        });
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      if (workflowState !== 'completed' && workflowState !== 'failed') {
        // Attempt reconnect with exponential backoff if not done
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt.current), 30000);
        reconnectAttempt.current += 1;
        console.log(`Reconnecting in ${delay}ms (Attempt ${reconnectAttempt.current})`);
        wsReconnectTimeout.current = setTimeout(() => {
          if (id) connectWebSocket(id);
        }, delay);
      }
    };
    
    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };
  };

  const addTimelineEvent = (time, message, type) => {
    setTimelineEvents(prev => [...prev, { time, message, type }]);
  };

  const handleStartAnalysis = async (e) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setSubview('graph');
    setWorkflowState('pending');
    setElapsedTime(0);
    setNodeStates({});
    setTimelineEvents([]);
    setGraph({ nodes: [], edges: [] });
    setActiveNodeId(null);

    // Start timer
    timerRef.current = setInterval(() => {
      setElapsedTime(prev => +(prev + 0.1).toFixed(1));
    }, 100);

    try {
      const decRes = await api.executeDecision(workspace?.id || 'ws1-uuid-0001', queryText);
      const id = decRes.id || decRes.decision_id;
      setDecisionId(id);
      
      if (decRes.graph) {
        setGraph(decRes.graph);
        // Initialize node states
        const initialStates = {};
        decRes.graph.nodes.forEach(n => {
          initialStates[n.id] = { status: 'pending', produced: [], consumed: [], stream: '' };
        });
        setNodeStates(initialStates);
      }
      
      connectWebSocket(id);

      window.__lastDecisionResult = decRes;
    } catch (err) {
      clearInterval(timerRef.current);
      toast.error(err.response?.data?.detail || 'Failed to execute decision.');
      setSubview('input');
    }
  };

  useEffect(() => {
    if (workflowState === 'completed' || workflowState === 'failed') {
      clearInterval(timerRef.current);
    }
  }, [workflowState]);

  useEffect(() => {
    return () => {
      clearInterval(timerRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleReviewClick = () => {
    onDecisionComplete(decisionId);
  };

  const activeNodeData = activeNodeId ? graph.nodes.find(n => n.id === activeNodeId) : null;
  const activeState = activeNodeId ? nodeStates[activeNodeId] : null;

  // Calculate overall progress based on completed nodes
  const totalNodes = graph.nodes.length || 1;
  const completedNodes = Object.values(nodeStates).filter(s => s.status === 'completed').length;
  const progress = Math.round((completedNodes / totalNodes) * 100);

  return (
    <div className="full-page-scroll">
      {subview === 'input' ? (
        <div className="decisions-landing">
          <h1>What decision would you like to make?</h1>
          <p className="subtitle">Describe your decision objective in natural language and our AI will analyze relevant knowledge to provide you with the best recommendations.</p>

          <form onSubmit={handleStartAnalysis} style={{ width: '100%' }}>
            <div className="decisions-prompt-card">
              <div className="decisions-prompt-textarea-wrapper">
                <textarea
                  placeholder="Recommend the best software vendor for our AI infrastructure."
                  value={queryText}
                  onChange={e => setQueryText(e.target.value)}
                  required
                />
                <div className="decisions-prompt-actions-inside">
                  <button type="button" className="decisions-prompt-btn-icon" onClick={() => setQueryText('Recommend the best software vendor for our AI infrastructure.')}>
                    <Lightbulb size={16} />
                  </button>
                  <button type="button" className="decisions-prompt-btn-icon" onClick={() => alert('Add attachment is currently in mock.')}>
                    <Paperclip size={16} />
                  </button>
                </div>
              </div>

              <div className="decisions-sources-label">Using knowledge from</div>
              <div className="decisions-sources-row">
                {sources.map(src => (
                  <div key={src.id} className={`decisions-source-pill ${src.active ? src.color : ''}`}>
                    <span>{src.name}</span>
                    <button type="button" className="remove-btn" onClick={() => setSources(prev => prev.map(s => s.id === src.id ? { ...s, active: !s.active } : s))}>
                      {src.active ? '✕' : '+'}
                    </button>
                  </div>
                ))}
                <button type="button" className="decisions-add-source-btn" onClick={() => alert('Choose source modal is currently in mock.')}>
                  <Plus size={12} /> Add Source
                </button>
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ padding: '14px 28px', fontSize: '15px' }}>
              <Play size={16} fill="currentColor" /> Start Analysis
            </button>
          </form>

          <div className="decisions-landing-footer" style={{ marginTop: '48px' }}>
            <ShieldAlert size={14} />
            <span>Your data is secure and private</span>
          </div>
        </div>
      ) : (
        /* Graph running view */
        <div>
          <div className="execution-header">
            <div className="execution-header-left">
              <h2>User Query</h2>
              <p className="query-text">"{queryText}"</p>
            </div>
            <div className="execution-header-right">
              {workflowState === 'running' || workflowState === 'pending' ? (
                <div className="execution-status-pill running">
                  <Loader2 size={16} className="inspector-agent-avatar running" />
                  <span>In Progress</span>
                </div>
              ) : workflowState === 'completed' ? (
                <div className="execution-status-pill completed">
                  <Check size={16} />
                  <span>Completed</span>
                </div>
              ) : (
                <div className="execution-status-pill error" style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.2)', backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                  <AlertTriangle size={16} />
                  <span>Failed</span>
                </div>
              )}
            </div>
          </div>

          <div className="execution-tabs-row">
            <button className="execution-tab-btn">Overview</button>
            <button className="execution-tab-btn active">Plan Graph</button>
            <button className="execution-tab-btn">Artifacts</button>
            <button className="execution-tab-btn">Explanation</button>
            <button className="execution-tab-btn" disabled={workflowState !== 'completed'} onClick={handleReviewClick}>
              Review
            </button>
          </div>

          <div className="execution-main-grid">
            <div className="execution-graph-panel">
              <div className="graph-zoom-controls">
                <button className="graph-zoom-btn">－</button>
                <button className="graph-zoom-btn">＋</button>
                <button className="graph-zoom-btn"><Maximize2 size={14} /></button>
              </div>

              <div className="graph-nodes-flow">
                {graph.nodes.map((node) => {
                  const state = nodeStates[node.id] || {};
                  const isCompleted = state.status === 'completed';
                  const isRunning = state.status === 'running';
                  const isFailed = state.status === 'failed';
                  
                  return (
                    <div key={node.id} className="graph-node-card-wrapper" onClick={() => setActiveNodeId(node.id)} style={{ cursor: 'pointer' }}>
                      <div className={`graph-node-card ${isCompleted ? 'completed' : ''} ${isRunning ? 'running' : ''} ${isFailed ? 'failed' : ''} ${activeNodeId === node.id ? 'active' : ''}`} style={isFailed ? { borderColor: 'var(--danger)' } : activeNodeId === node.id ? { borderColor: 'var(--primary)', boxShadow: '0 0 0 2px rgba(99, 102, 241, 0.2)' } : {}}>
                        <div className="graph-node-indicator">
                          {isCompleted ? <Check size={14} strokeWidth={3} /> : (isRunning ? <Loader2 size={14} className="inspector-agent-avatar running" /> : isFailed ? <AlertTriangle size={14} color="var(--danger)" /> : <div />)}
                        </div>
                        
                        <div className="graph-node-text">
                          <h4>{node.agent || node.id}</h4>
                          <p className="meta">{state.status === 'pending' ? 'Pending' : (state.duration ? `${state.duration}ms` : 'Running')}</p>
                          <p className="desc">{node.objective || node.description}</p>
                        </div>
                      </div>

                      <div className="graph-node-connector-arrow">
                        <div className="graph-node-connector-line"></div>
                        {node.produces?.length > 0 && (
                          <div className="graph-node-outputs">
                            {node.produces.map(art => {
                              const isArtCreated = state.produced?.includes(art);
                              return (
                                <span key={art} className={`graph-node-output-pill ${isArtCreated ? 'completed' : ''} ${isRunning && !isArtCreated ? 'running' : ''}`}>
                                  {art}
                                </span>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="execution-inspector-panel">
              {activeNodeData ? (
                <div>
                  <div className="inspector-agent-header">
                    <div className={`inspector-agent-avatar ${activeState?.status === 'running' ? 'running' : ''}`} style={activeState?.status === 'failed' ? { backgroundColor: 'var(--danger-dim)', color: 'var(--danger)' } : {}}>
                      {activeState?.status === 'running' ? <Loader2 size={22} /> : activeState?.status === 'completed' ? <Check size={22} /> : activeState?.status === 'failed' ? <AlertTriangle size={22} /> : <div />}
                    </div>
                    <div className="inspector-agent-title">
                      <h3>{activeNodeData.agent || activeNodeData.id}</h3>
                      <span className="status">{activeState?.status || 'pending'}</span>
                    </div>
                  </div>

                  <table className="inspector-details-table">
                    <tbody>
                      <tr>
                        <td className="label">Execution Time</td>
                        <td className="value">{activeState?.duration ? `${activeState.duration}ms` : (activeState?.status === 'running' ? '...' : '-')}</td>
                      </tr>
                      <tr>
                        <td className="label">Status</td>
                        <td className="value" style={{ color: activeState?.status === 'running' ? 'var(--primary)' : activeState?.status === 'completed' ? 'var(--success)' : activeState?.status === 'failed' ? 'var(--danger)' : activeState?.status === 'skipped' ? 'var(--text-secondary)' : 'var(--text-secondary)' }}>
                          {activeState?.status?.toUpperCase() || 'PENDING'}
                        </td>
                      </tr>
                      {activeState?.metrics?.retrieved_chunk_count !== undefined && (
                      <tr>
                        <td className="label">Chunks Retrieved</td>
                        <td className="value">{activeState.metrics.retrieved_chunk_count}</td>
                      </tr>
                      )}
                      {activeState?.metrics?.confidence_score !== undefined && (
                      <tr>
                        <td className="label">Confidence Score</td>
                        <td className="value">{activeState.metrics.confidence_score}</td>
                      </tr>
                      )}
                    </tbody>
                  </table>

                  <div className="inspector-description-box">
                    <h4>Description</h4>
                    <p>{activeNodeData.description}</p>
                  </div>

                  <div className="inspector-description-box">
                    <h4>Artifacts</h4>
                    <div className="inspector-artifacts-list">
                      {activeNodeData.consumes?.map(art => (
                         <span key={art} className="inspector-artifact-tag" style={{ borderLeft: '2px solid var(--primary)' }}>↓ {art}</span>
                      ))}
                      {activeNodeData.produces?.map(art => (
                         <span key={art} className="inspector-artifact-tag" style={{ borderLeft: '2px solid var(--success)' }}>↑ {art}</span>
                      ))}
                    </div>
                  </div>
                  
                  {activeState?.stream && (
                    <div className="inspector-description-box">
                      <h4>Streaming Output</h4>
                      <p style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', backgroundColor: 'var(--surface-sunken)', padding: '8px', borderRadius: '4px' }}>
                        {activeState.stream}
                      </p>
                    </div>
                  )}
                  
                  {activeState?.error && (
                    <div className="inspector-description-box" style={{ borderColor: 'rgba(239, 68, 68, 0.2)' }}>
                      <h4 style={{ color: 'var(--danger)' }}>Error</h4>
                      <p style={{ color: 'var(--danger)' }}>{activeState.error}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                  Select a node to inspect its execution details.
                </div>
              )}

              <div>
                <div className="inspector-progress-section">
                  <div className="inspector-progress-label">
                    <span>Overall Execution</span>
                    <span>{elapsedTime}s</span>
                  </div>
                  <div className="inspector-progress-bar">
                    <div className="inspector-progress-fill" style={{ width: `${progress}%` }}></div>
                  </div>
                </div>

                {workflowState === 'completed' && (
                  <button className="btn btn-primary" style={{ width: '100%', marginTop: '20px', padding: '12px' }} onClick={handleReviewClick}>
                    Review Recommendation
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="execution-timeline-card">
            <h3>Execution Timeline</h3>
            <div className="timeline-track" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '16px 0' }}>
              {timelineEvents.map((evt, idx) => (
                <div key={idx} style={{ display: 'flex', gap: '12px', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-tertiary)', minWidth: '70px' }}>{evt.time}</span>
                  <span style={{ color: evt.type === 'success' ? 'var(--success)' : evt.type === 'error' ? 'var(--danger)' : 'var(--text-primary)' }}>
                    {evt.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
