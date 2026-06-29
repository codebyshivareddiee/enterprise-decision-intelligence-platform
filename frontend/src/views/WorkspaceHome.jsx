import React, { useState, useEffect } from 'react';
import { HelpCircle, ChevronRight, UploadCloud, PlusSquare, FileText, UserPlus, ArrowRight, ShieldAlert, Sparkles } from 'lucide-react';
import { api } from '../services/api';

export default function WorkspaceHome({ workspace, onNavigateTab, onSelectDecision, onTriggerUpload }) {
  const [decisions, setDecisions] = useState([]);
  const [rules, setRules] = useState([]);
  const [queryInput, setQueryInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (workspace?.id) {
      loadWorkspaceDashboard();
    }
  }, [workspace?.id]);

  const loadWorkspaceDashboard = async () => {
    setLoading(true);
    const fetchedDecisions = await api.getDecisions(workspace.id);
    const fetchedRules = await api.getRules(workspace.id);
    setDecisions(fetchedDecisions);
    setRules(fetchedRules);
    setLoading(false);
  };

  const handleSuggestionClick = (query) => {
    onNavigateTab('decisions', query);
  };

  const handleQuerySubmit = (e) => {
    e.preventDefault();
    if (!queryInput.trim()) return;
    onNavigateTab('decisions', queryInput);
  };

  return (
    <div className="workspace-content">
      {/* Left Column (Main Section) */}
      <div className="workspace-left-section">
        {/* Welcome message */}
        <div style={{ marginBottom: '8px' }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 700 }}>
            Welcome back, Alex! 👋
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '13.5px' }}>
            Here's what's happening in {workspace?.name || 'your workspace'}.
          </p>
        </div>

        {/* Start New Decision input card */}
        <div className="query-card">
          <div className="query-card-header">
            <div className="query-card-icon">
              <Sparkles size={20} />
            </div>
            <div className="query-card-header-text">
              <h3>Start a new decision</h3>
              <p>Ask a question or describe the decision you need to make.</p>
            </div>
            <button className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto' }}>
              Customize Home
            </button>
          </div>

          <form onSubmit={handleQuerySubmit}>
            <div className="query-input-container">
              <div className="query-input-wrapper">
                <HelpCircle size={18} className="query-input-icon" />
                <input
                  type="text"
                  placeholder="What decision would you like to make?"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                />
              </div>
              <button type="submit" className="query-submit-btn">
                <ArrowRight size={16} />
              </button>
            </div>
          </form>

          {/* Suggestion Chips */}
          <div className="query-suggestions-row">
            <button className="suggestion-chip" onClick={() => handleSuggestionClick('Recommend the best software vendor for our AI infrastructure.')}>
              Vendor Selection
            </button>
            <button className="suggestion-chip" onClick={() => handleSuggestionClick('Review the data storage compliance policy for GDPR.')}>
              Policy Review
            </button>
            <button className="suggestion-chip" onClick={() => handleSuggestionClick('Allocate resource budget for server optimization.')}>
              Resource Allocation
            </button>
            <button className="suggestion-chip" onClick={() => handleSuggestionClick('Analyze compliance risk under current system regulations.')}>
              Risk Assessment
            </button>
            <button className="suggestion-chip" onClick={() => onNavigateTab('decisions')}>
              + Custom
            </button>
          </div>
        </div>

        {/* Quick Actions widget */}
        <div className="widget-card">
          <div className="widget-card-header">
            <h3>Quick actions</h3>
            <a href="#view-all" className="widget-card-header-link" onClick={(e) => { e.preventDefault(); onNavigateTab('knowledge'); }}>
              View all
            </a>
          </div>

          <div className="quick-actions-grid">
            <div className="quick-action-button" onClick={onTriggerUpload}>
              <div className="quick-action-icon-wrapper"><UploadCloud size={20} /></div>
              <h4>Upload Knowledge</h4>
              <p>Add documents, policies, and data sources</p>
            </div>

            <div className="quick-action-button" onClick={() => onNavigateTab('decisions')}>
              <div className="quick-action-icon-wrapper"><PlusSquare size={20} /></div>
              <h4>Create Decision</h4>
              <p>Start a new decision from scratch</p>
            </div>

            <div className="quick-action-button" onClick={() => onNavigateTab('settings')}>
              <div className="quick-action-icon-wrapper"><FileText size={20} /></div>
              <h4>Apply Business Rules</h4>
              <p>Manage rules and constraints</p>
            </div>

            <div className="quick-action-button" onClick={() => alert('Invite members module is currently in mock.')}>
              <div className="quick-action-icon-wrapper"><UserPlus size={20} /></div>
              <h4>Invite Members</h4>
              <p>Add collaborators to your workspace</p>
            </div>
          </div>
        </div>

        {/* Recent Decisions list */}
        <div className="widget-card">
          <div className="widget-card-header">
            <h3>Recent Decisions</h3>
            <a href="#view-decisions" className="widget-card-header-link" onClick={(e) => { e.preventDefault(); onNavigateTab('decisions'); }}>
              View all
            </a>
          </div>

          <div className="dashboard-decisions-list">
            {decisions.map((dec) => (
              <div key={dec.id} className="dashboard-decision-row" onClick={() => onSelectDecision(dec)}>
                <div className="decision-row-left">
                  <div className={`decision-indicator-dot ${dec.status}`}></div>
                  <div className="decision-details-summary">
                    <h4>{dec.name}</h4>
                    <div className="decision-details-sub">
                      <span className="code">{dec.code || 'DEC-RUN'}</span>
                      <span>•</span>
                      <span>{dec.decided_by_name || 'AI Assistant'}</span>
                      <span>•</span>
                      <span>{dec.date}</span>
                    </div>
                  </div>
                </div>
                <div className="decision-row-right">
                  <div className="decision-confidence-tag">
                    {dec.confidence}% Confidence
                  </div>
                  <span className={`decision-outcome-badge ${dec.status}`}>
                    {dec.status}
                  </span>
                  <ChevronRight size={16} />
                </div>
              </div>
            ))}
            {decisions.length === 0 && (
              <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text-muted)' }}>
                No decisions yet in this workspace. Enter a query above to execute your first decision!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Column (Overview Section) */}
      <div className="workspace-right-section">
        {/* Knowledge Overview list */}
        <div className="widget-card">
          <div className="widget-card-header">
            <h3>Knowledge Overview</h3>
            <a href="#view-knowledge" className="widget-card-header-link" onClick={(e) => { e.preventDefault(); onNavigateTab('knowledge'); }}>
              View all
            </a>
          </div>

          <div className="knowledge-overview-list">
            <div className="knowledge-overview-row">
              <span className="knowledge-overview-type">
                <FileText size={16} /> Documents
              </span>
              <span className="knowledge-overview-count">1,248</span>
            </div>
            <div className="knowledge-overview-row">
              <span className="knowledge-overview-type">
                <FileText size={16} style={{ color: 'var(--success)' }} /> Policies
              </span>
              <span className="knowledge-overview-count">342</span>
            </div>
            <div className="knowledge-overview-row">
              <span className="knowledge-overview-type">
                <FileText size={16} style={{ color: '#7c3aed' }} /> Business Rules
              </span>
              <span className="knowledge-overview-count">{rules.length || 156}</span>
            </div>
            <div className="knowledge-overview-row">
              <span className="knowledge-overview-type">
                <FileText size={16} style={{ color: '#f59e0b' }} /> Data Sources
              </span>
              <span className="knowledge-overview-count">28</span>
            </div>
            <div className="knowledge-overview-row">
              <span className="knowledge-overview-type">
                <FileText size={16} style={{ color: '#ec4899' }} /> Templates
              </span>
              <span className="knowledge-overview-count">19</span>
            </div>
          </div>

          <a href="#knowledge-link" className="stats-card-footer-link" style={{ marginTop: '24px' }} onClick={(e) => { e.preventDefault(); onNavigateTab('knowledge'); }}>
            <span>Go to knowledge</span>
            <ArrowRight size={14} />
          </a>
        </div>

        {/* Compliance Footer info */}
        <div className="compliance-banner-footer" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '12px' }}>
          <div className="compliance-banner-left">
            <div className="compliance-banner-icon"><ShieldAlert size={16} /></div>
            <strong>Workspace is secure and compliant</strong>
          </div>
          <div className="compliance-banner-tags" style={{ flexWrap: 'wrap' }}>
            <span>SOC 2 Type II</span>
            <span>ISO 27001</span>
            <span>Encrypted</span>
            <span>Role-based access</span>
          </div>
          <a href="#security-center" className="compliance-banner-link" onClick={(e) => e.preventDefault()}>
            View security center ›
          </a>
        </div>
      </div>
    </div>
  );
}
