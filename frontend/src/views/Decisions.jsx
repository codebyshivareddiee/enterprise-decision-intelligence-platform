import React, { useState, useEffect } from 'react';
import { HelpCircle, Paperclip, Lightbulb, ArrowRight, ShieldAlert, Check, Play, PlayCircle, Loader2, Maximize2, Plus } from 'lucide-react';
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

  // Simulated execution states
  const [activeStep, setActiveStep] = useState(0); // 0: Retriever, 1: Reasoning, 2: Recommendation, 3: Rule Checker, 4: Explanation, 5: Complete
  const [stepStates, setStepStates] = useState([
    { id: 0, name: 'Retriever Agent', desc: 'Retrieves relevant knowledge from selected sources.', status: 'pending', time: 'Pending', count: 'Not started', output: 'RETRIEVED_CHUNKS' },
    { id: 1, name: 'Reasoning Agent', desc: 'Analyzes retrieved content and derives key insights.', status: 'pending', time: 'Pending', count: 'Not started', output: 'REASONING_RESULT' },
    { id: 2, name: 'Recommendation Agent', desc: 'Generates recommendation based on reasoning and business context.', status: 'pending', time: 'Pending', count: 'Not started', output: 'RECOMMENDATION' },
    { id: 3, name: 'Rule Checker Agent', desc: 'Validates the recommendation against business rules and constraints.', status: 'pending', time: 'Pending', count: 'Not started', output: 'VALIDATION_RESULT' },
    { id: 4, name: 'Explanation Agent', desc: 'Creates a natural language explanation of the final decision.', status: 'pending', time: 'Pending', count: 'Not started', output: 'EXPLANATION' }
  ]);

  const [progress, setProgress] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [decisionId, setDecisionId] = useState(null);

  useEffect(() => {
    if (initialQuery) {
      setQueryText(initialQuery);
    }
  }, [initialQuery]);

  const handleStartAnalysis = async (e) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setSubview('graph');
    setProgress(0);
    setActiveStep(0);
    setElapsedTime(0);

    try {
      // Call execute decision on backend
      const decRes = await api.executeDecision(workspace?.id || 'ws1-uuid-0001', queryText);
      setDecisionId(decRes.id || decRes.decision_id);

      // Reset steps state to completed
      setStepStates([
        { id: 0, name: 'Retriever Agent', desc: 'Retrieves relevant knowledge from selected sources.', status: 'completed', time: 'Completed', count: 'Chunks retrieved', output: 'RETRIEVED_CHUNKS' },
        { id: 1, name: 'Reasoning Agent', desc: 'Analyzes retrieved content and derives key insights.', status: 'completed', time: 'Completed', count: 'Analysis complete', output: 'REASONING_RESULT' },
        { id: 2, name: 'Recommendation Agent', desc: 'Generates recommendation based on reasoning and business context.', status: 'completed', time: 'Completed', count: 'Recommendation ready', output: 'RECOMMENDATION' },
        { id: 3, name: 'Rule Checker Agent', desc: 'Validates the recommendation against business rules and constraints.', status: 'completed', time: 'Completed', count: 'Rules verified', output: 'VALIDATION_RESULT' },
        { id: 4, name: 'Explanation Agent', desc: 'Creates a natural language explanation of the final decision.', status: 'completed', time: 'Completed', count: 'Explanation finalized', output: 'EXPLANATION' }
      ]);
      
      setProgress(100);
      setActiveStep(5);
      
      // Store the result so Review can use it
      window.__lastDecisionResult = decRes;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to execute decision.');
      setSubview('input');
    }
  };

  // Removed simulated timers to rely on synchronous backend call

  const handleReviewClick = () => {
    // call final complete callback
    onDecisionComplete(decisionId);
  };

  useEffect(() => {
    let interval = null;
    if (subview === 'graph' && activeStep < 5) {
      interval = setInterval(() => {
        setElapsedTime(prev => +(prev + 0.1).toFixed(1));
      }, 100);
    }
    return () => clearInterval(interval);
  }, [subview, activeStep]);

  const activeAgent = stepStates[Math.min(activeStep, 4)];

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

              {/* Sources tags selection */}
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
          {/* Header */}
          <div className="execution-header">
            <div className="execution-header-left">
              <h2>User Query</h2>
              <p className="query-text">"{queryText}"</p>
            </div>
            <div className="execution-header-right">
              {activeStep < 5 ? (
                <div className="execution-status-pill running">
                  <Loader2 size={16} className="inspector-agent-avatar running" />
                  <span>In Progress</span>
                </div>
              ) : (
                <div className="execution-status-pill completed">
                  <Check size={16} />
                  <span>Completed</span>
                </div>
              )}
            </div>
          </div>

          {/* Sub-tabs */}
          <div className="execution-tabs-row">
            <button className="execution-tab-btn">Overview</button>
            <button className="execution-tab-btn active">Plan Graph</button>
            <button className="execution-tab-btn">Artifacts</button>
            <button className="execution-tab-btn">Explanation</button>
            <button className="execution-tab-btn" disabled={activeStep < 5} onClick={handleReviewClick}>
              Review
            </button>
          </div>

          {/* Main Grid */}
          <div className="execution-main-grid">
            {/* Graph flow middle panel */}
            <div className="execution-graph-panel">
              <div className="graph-zoom-controls">
                <button className="graph-zoom-btn">－</button>
                <button className="graph-zoom-btn">＋</button>
                <button className="graph-zoom-btn"><Maximize2 size={14} /></button>
              </div>

              <div className="graph-nodes-flow">
                {stepStates.map((step, index) => {
                  const isCompleted = step.status === 'completed';
                  const isRunning = step.status === 'running' || (index === activeStep && activeStep < 5);
                  
                  return (
                    <div key={step.id} className="graph-node-card-wrapper">
                      <div className={`graph-node-card ${isCompleted ? 'completed' : ''} ${isRunning ? 'running' : ''}`}>
                        <div className="graph-node-indicator">
                          {isCompleted ? <Check size={14} strokeWidth={3} /> : (isRunning ? <Loader2 size={14} className="inspector-agent-avatar running" /> : <div />)}
                        </div>
                        
                        <div className="graph-node-text">
                          <h4>{step.name}</h4>
                          <p className="meta">{step.time} • {step.count}</p>
                          <p className="desc">{step.desc}</p>
                        </div>
                      </div>

                      <div className="graph-node-connector-arrow">
                        <div className="graph-node-connector-line"></div>
                        <span className={`graph-node-output-pill ${isCompleted ? 'completed' : ''} ${isRunning ? 'running' : ''}`}>
                          {step.output}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right details inspector */}
            <div className="execution-inspector-panel">
              <div>
                <div className="inspector-agent-header">
                  <div className={`inspector-agent-avatar ${activeStep < 5 ? 'running' : ''}`}>
                    {activeStep < 5 ? <Loader2 size={22} /> : <Check size={22} />}
                  </div>
                  <div className="inspector-agent-title">
                    <h3>{activeStep < 5 ? activeAgent?.name : 'Decision Process Finished'}</h3>
                    <span className="status">{activeStep < 5 ? 'Running' : 'Ready'}</span>
                  </div>
                </div>

                <table className="inspector-details-table">
                  <tbody>
                    <tr>
                      <td className="label">Execution Time</td>
                      <td className="value">{elapsedTime}s</td>
                    </tr>
                    <tr>
                      <td className="label">Status</td>
                      <td className="value" style={{ color: activeStep < 5 ? 'var(--primary)' : 'var(--success)' }}>
                        {activeStep < 5 ? 'In Progress' : 'Completed'}
                      </td>
                    </tr>
                    <tr>
                      <td className="label">Produced Outputs</td>
                      <td className="value">
                        <span className="graph-node-output-pill completed">
                          {activeStep < 5 ? activeAgent?.output : 'FINAL_REPORT'}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>

                <div className="inspector-description-box">
                  <h4>Description</h4>
                  <p>{activeStep < 5 ? activeAgent?.desc : 'All workflow execution plan nodes successfully resolved. Click Review to evaluate final recommendations and business rules.'}</p>
                </div>

                <div className="inspector-description-box">
                  <h4>Input Artifacts</h4>
                  <div className="inspector-artifacts-list">
                    {activeStep === 0 && <span className="inspector-artifact-tag">USER_GOAL</span>}
                    {activeStep === 1 && <span className="inspector-artifact-tag">RETRIEVED_CHUNKS</span>}
                    {activeStep === 2 && (
                      <>
                        <span className="inspector-artifact-tag">RETRIEVED_CHUNKS</span>
                        <span className="inspector-artifact-tag">REASONING_RESULT</span>
                      </>
                    )}
                    {activeStep === 3 && <span className="inspector-artifact-tag">RECOMMENDATION</span>}
                    {activeStep === 4 && (
                      <>
                        <span className="inspector-artifact-tag">RECOMMENDATION</span>
                        <span className="inspector-artifact-tag">VALIDATION_RESULT</span>
                      </>
                    )}
                    {activeStep >= 5 && <span className="inspector-artifact-tag">EXPLANATION</span>}
                  </div>
                </div>
              </div>

              <div>
                <div className="inspector-progress-section">
                  <div className="inspector-progress-label">
                    <span>Progress</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="inspector-progress-bar">
                    <div className="inspector-progress-fill" style={{ width: `${progress}%` }}></div>
                  </div>
                </div>

                {activeStep >= 5 && (
                  <button className="btn btn-primary" style={{ width: '100%', marginTop: '20px', padding: '12px' }} onClick={handleReviewClick}>
                    Review Recommendation
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Bottom Execution Timeline */}
          <div className="execution-timeline-card">
            <h3>Execution Timeline</h3>
            <div className="timeline-track">
              {stepStates.map((step, index) => (
                <div key={step.id} className={`timeline-step ${step.status === 'completed' ? 'completed' : ''} ${step.status === 'running' ? 'running' : ''}`}>
                  <div className="timeline-step-dot">
                    {step.status === 'completed' ? <Check size={12} strokeWidth={3} /> : index + 1}
                  </div>
                  <h4>{step.name.split(' ')[0]}</h4>
                  <p>{step.time}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
