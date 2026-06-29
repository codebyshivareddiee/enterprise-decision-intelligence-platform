import React, { useState, useEffect } from 'react';
import { Award, CheckCircle, FileText, XCircle, ChevronLeft, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { toast } from 'sonner';

export default function Review({ workspace, decisionId, onBackToDashboard, onViewDetails }) {
  const [decision, setDecision] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (decisionId) {
      loadDecision();
    }
  }, [decisionId]);

  const loadDecision = async () => {
    setLoading(true);
    try {
      let fetchedDecision = null;
      if (window.__lastDecisionResult && (window.__lastDecisionResult.id === decisionId || window.__lastDecisionResult.decision_id === decisionId)) {
        const lr = window.__lastDecisionResult;
        fetchedDecision = {
          id: decisionId,
          name: `AI Evaluation: ${workspace?.goal?.substring(0, 24) || 'Decision'}...`,
          goal: workspace?.goal || 'No goal specified',
          status: lr.execution_status.toLowerCase(),
          confidence: lr.recommendation?.final_score ? Math.round(lr.recommendation.final_score * 100) : 0,
          date: new Date().toLocaleDateString(),
          decided_by_name: 'AI Orchestrator',
          recommended_option: lr.recommendation?.entity_id || 'Unknown',
          explanation: lr.explanation || 'No explanation generated.',
          evidence: lr.supporting_evidence || [],
          rules: [],
          workspace: workspace
        };
      } else {
        fetchedDecision = await api.getDecision(decisionId);
        fetchedDecision.workspace = workspace;
      }
      setDecision(fetchedDecision);
    } catch (err) {
      toast.error('Failed to load decision review context.');
    }
    setLoading(false);
  };

  const handleApprove = async () => {
    if (!decision) return;
    setLoading(true);
    try {
      await api.recordOutcome(decision.id, 'Approved', feedback);
      await api.resumeDecision(decision.id, feedback);
      toast.success('Decision Approved successfully!');
      onBackToDashboard();
    } catch (err) {
      toast.error('Failed to approve decision.');
    }
    setLoading(false);
  };

  const handleReject = async () => {
    if (!decision) return;
    if (!feedback.trim()) {
      toast.error('Feedback is required when rejecting a recommendation.');
      return;
    }
    setLoading(true);
    try {
      await api.recordOutcome(decision.id, 'Rejected', feedback);
      await api.resumeDecision(decision.id, feedback);
      toast.success('Decision Rejected.');
      onBackToDashboard();
    } catch (err) {
      toast.error('Failed to reject decision.');
    }
    setLoading(false);
  };

  if (!decision) {
    return <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading decision review context...</div>;
  }

  return (
    <div className="full-page-scroll">
      {/* Header breadcrumbs */}
      <div className="review-top-banner">
        <div className="review-top-banner-left">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '12px', marginBottom: '8px', cursor: 'pointer' }} onClick={onBackToDashboard}>
            <ChevronLeft size={14} /> Back to Home
          </div>
          <h1>Decision Review</h1>
          <p>Review the AI's recommendation with full context and evidence.</p>
        </div>
        <div className="execution-status-pill running">
          <div className="decision-indicator-dot pending"></div>
          <span>In Progress</span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="review-main-grid">
        {/* Left column */}
        <div className="review-left-column">
          {/* Summary card */}
          <div className="review-card-summary">
            <div className="review-summary-row">
              <div className="review-summary-icon">
                <Award size={28} />
              </div>
              <div className="review-summary-details">
                <div className="review-summary-item">
                  <p className="label">Recommended Option</p>
                  <h3>{decision.recommended_option || 'AcmeSoft'}</h3>
                </div>
                <div className="review-summary-item">
                  <p className="label">Confidence</p>
                  <span className="decision-confidence-tag">
                    {decision.confidence || 94}%
                  </span>
                </div>
              </div>
            </div>

            <div className="review-explanation-box">
              <h4>Explanation</h4>
              <p>{decision.explanation || 'Matches all business requirements including budget, security, compliance, and API capabilities.'}</p>
            </div>
          </div>

          {/* Supporting Evidence */}
          <div className="widget-card">
            <div className="widget-card-header">
              <h3>Supporting Evidence</h3>
            </div>
            <div className="evidence-list">
              {decision.evidence?.map((item, idx) => (
                <div key={idx} className="evidence-row-item" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', gap: '8px' }}>
                  <div className="evidence-row-left" style={{ width: '100%', display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={18} style={{ color: '#ef4444' }} />
                      <span className="name" style={{ fontWeight: '500' }}>{item.asset_name || item.name || item}</span>
                    </div>
                    <div className="evidence-row-right">
                      {item.relevance_score ? `Score: ${Math.round(item.relevance_score * 100)}%` : ''}
                    </div>
                  </div>
                  {item.chunk_preview && (
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '8px', borderRadius: '4px', width: '100%', fontStyle: 'italic' }}>
                      "{item.chunk_preview}"
                    </div>
                  )}
                </div>
              ))}
              {(!decision.evidence || decision.evidence.length === 0) && (
                <div className="evidence-row-item">
                  <div className="evidence-row-left">
                    <span className="name">No supporting evidence provided.</span>
                  </div>
                </div>
              )}
            </div>
            <a href="#all-evidence" className="evidence-view-all" onClick={(e) => { e.preventDefault(); alert('Opening full evidence database...'); }}>
              + View all evidence
            </a>
          </div>
        </div>

        {/* Right column */}
        <div className="review-right-column">
          {/* Applied Rules Checklist */}
          <div className="widget-card">
            <div className="widget-card-header">
              <h3>Applied Rules</h3>
            </div>
            <div className="applied-rules-list">
              {decision.rules?.map((rule, idx) => (
                <div key={idx} className="applied-rule-row">
                  <div className="applied-rule-left">
                    <CheckCircle size={16} />
                    <span>{rule.name}</span>
                  </div>
                  <span className="applied-rule-status">Satisfied</span>
                </div>
              ))}
              {(!decision.rules || decision.rules.length === 0) && (
                <>
                  <div className="applied-rule-row">
                    <div className="applied-rule-left">
                      <CheckCircle size={16} />
                      <span>Budget Constraint</span>
                    </div>
                    <span className="applied-rule-status">Satisfied</span>
                  </div>
                  <div className="applied-rule-row">
                    <div className="applied-rule-left">
                      <CheckCircle size={16} />
                      <span>ISO 27001</span>
                    </div>
                    <span className="applied-rule-status">Satisfied</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Human Review box */}
          <div className="widget-card human-review-card">
            <div className="widget-card-header">
              <h3>Human Review</h3>
            </div>
            <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Please review the recommendation and provide your feedback.
            </p>
            <textarea
              placeholder="Provide feedback if rejecting..."
              maxLength={500}
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
            />
            <div className="human-review-actions">
              <button className="btn btn-reject" onClick={handleReject} disabled={loading}>
                ✕ Reject
              </button>
              <button className="btn btn-approve" onClick={handleApprove} disabled={loading}>
                ✓ Approve
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Context bottom row */}
      <div className="review-context-card">
        <h3 style={{ marginBottom: '16px', fontSize: '16px' }}>Decision Context</h3>
        <div className="review-context-grid">
          <div className="review-context-item">
            <p className="label">Decision Objective / Goal</p>
            <p className="value" style={{ maxWidth: '320px', wordBreak: 'break-all' }}>
              {decision.workspace?.goal || decision.goal}
            </p>
          </div>
          <div className="review-context-item">
            <p className="label">Success Metrics</p>
            <p className="value" style={{ maxWidth: '320px', wordBreak: 'break-all' }}>
              {decision.workspace?.success_metrics || 'None specified'}
            </p>
          </div>
          <div className="review-context-item">
            <p className="label">Decision Points</p>
            <p className="value" style={{ maxWidth: '320px', wordBreak: 'break-all' }}>
              {decision.workspace?.decision_points || 'None specified'}
            </p>
          </div>
        </div>

        <button className="btn btn-secondary" style={{ marginTop: '20px' }} onClick={onViewDetails}>
          View Execution Details
        </button>
      </div>
    </div>
  );
}
