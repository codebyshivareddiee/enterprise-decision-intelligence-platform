import React, { useState, useEffect } from 'react';
import { Clock, CheckSquare, Award, UserCheck, MessageSquare } from 'lucide-react';
import { api } from '../services/api';
import { toast } from 'sonner';

export default function History({ workspace }) {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (workspace?.id) {
      loadHistory();
    }
  }, [workspace?.id]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const fetched = await api.getDecisions(workspace.id);
      setDecisions(fetched.filter(d => d.status !== 'pending'));
    } catch (err) {
      toast.error('Failed to load history.');
    }
    setLoading(false);
  };

  return (
    <div className="full-page-scroll">
      <div className="org-hub-welcome">
        <h1>History</h1>
        <p>Permanent append-only record of all decisions made in this workspace.</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>Loading history logs...</div>
      ) : (
        <div className="history-list">
          {decisions.map((dec) => (
            <div key={dec.id} className="history-card">
              <div className="history-card-header">
                <div className="history-card-header-left">
                  <Clock size={18} style={{ color: 'var(--primary)' }} />
                  <div>
                    <h3>{dec.name}</h3>
                    <p className="meta">{dec.code} • Initiated by {dec.decided_by_name} on {dec.date}</p>
                  </div>
                </div>
                <span className={`decision-outcome-badge ${dec.status}`}>
                  {dec.status}
                </span>
              </div>

              <div className="history-body-grid">
                <div className="history-body-section">
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Award size={14} /> AI Recommendation
                  </h4>
                  <div style={{ marginTop: '8px', padding: '12px', border: '1px solid var(--border)', borderRadius: '6px', backgroundColor: 'var(--bg-main)' }}>
                    <strong style={{ fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                      Recommended Option: {dec.recommended_option} ({dec.confidence}% Confidence)
                    </strong>
                    <p style={{ fontSize: '12.5px', color: 'var(--text-muted)' }}>{dec.explanation}</p>
                  </div>
                </div>

                <div className="history-body-section">
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <UserCheck size={14} /> Human Audit Outcome
                  </h4>
                  <div style={{ marginTop: '8px', padding: '12px', border: '1px solid var(--border)', borderRadius: '6px', backgroundColor: 'var(--bg-main)' }}>
                    <strong style={{ fontSize: '13px', display: 'block', marginBottom: '4px', color: dec.status === 'approved' ? 'var(--success)' : 'var(--danger)' }}>
                      Decision Outcome: {dec.status.toUpperCase()}
                    </strong>
                    <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', display: 'flex', alignItems: 'flex-start', gap: '6px', marginTop: '6px' }}>
                      <MessageSquare size={14} style={{ marginTop: '2px', flexShrink: 0 }} />
                      <span>{dec.feedback || 'No review notes supplied.'}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {decisions.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px', border: '1px dashed var(--border)', borderRadius: '8px', backgroundColor: 'var(--bg-card)', color: 'var(--text-muted)' }}>
              No decisions have been finalized in this workspace yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
