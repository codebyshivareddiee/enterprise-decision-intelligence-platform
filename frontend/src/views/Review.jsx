import React, { useState, useEffect } from 'react';
import { Award, CheckCircle, FileText, XCircle, ChevronLeft, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

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
    const fetchedDecision = await api.getDecision(decisionId);
    setDecision(fetchedDecision);
    setLoading(false);
  };

  const handleApprove = async () => {
    if (!decision) return;
    setLoading(true);
    await api.recordOutcome(decision.id, 'Approved', feedback);
    await api.resumeDecision(decision.id, feedback);
    alert('Decision Approved successfully!');
    onBackToDashboard();
    setLoading(false);
  };

  const handleReject = async () => {
    if (!decision) return;
    if (!feedback.trim()) {
      alert('Feedback is required when rejecting a recommendation.');
      return;
    }
    setLoading(true);
    await api.recordOutcome(decision.id, 'Rejected', feedback);
    await api.resumeDecision(decision.id, feedback);
    alert('Decision Rejected.');
    onBackToDashboard();
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
            <ChevronLeft size={14} /> Back to Decisions
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
              {decision.evidence?.map((file, idx) => (
                <div key={idx} className="evidence-row-item">
                  <div className="evidence-row-left">
                    <FileText size={18} style={{ color: '#ef4444' }} />
                    <span className="name">{file}</span>
                  </div>
                  <div className="evidence-row-right">
                    {idx === 0 ? '12 pages' : (idx === 1 ? '18 pages' : '24 pages')}
                  </div>
                </div>
              ))}
              {(!decision.evidence || decision.evidence.length === 0) && (
                <div className="evidence-row-item">
                  <div className="evidence-row-left">
                    <FileText size={18} style={{ color: '#ef4444' }} />
                    <span className="name">Vendor_Profile.pdf</span>
                  </div>
                  <div className="evidence-row-right">12 pages</div>
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
        <div className="review-context-grid">
          <div className="review-context-item">
            <p className="label">Decision Name</p>
            <p className="value">{decision.name}</p>
          </div>
          <div className="review-context-item">
            <p className="label">Decision Objective</p>
            <p className="value" style={{ maxWidth: '320px', wordBreak: 'break-all' }}>
              {decision.goal}
            </p>
          </div>
          <div className="review-context-item">
            <p className="label">Requested By</p>
            <p className="value">
              {decision.decided_by_name || 'Alex Johnson'} on {decision.date || 'May 20, 2025'}
            </p>
          </div>
        </div>

        <button className="btn btn-secondary" onClick={onViewDetails}>
          View Execution Details
        </button>
      </div>
    </div>
  );
}
