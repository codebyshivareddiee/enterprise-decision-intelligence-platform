import React, { useState, useEffect } from 'react';
import { PlusCircle, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { toast } from 'sonner';

export default function Settings({ workspace, user, setWorkspaces }) {
  const [activePane, setActivePane] = useState('workspace');
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(false);

  // Workspace fields
  const [wsName, setWsName] = useState('');
  const [wsDesc, setWsDesc] = useState('');
  const [wsGoal, setWsGoal] = useState('');
  const [wsSuccessMetrics, setWsSuccessMetrics] = useState('');
  const [wsDecisionPoints, setWsDecisionPoints] = useState('');
  const [isSavingWs, setIsSavingWs] = useState(false);

  useEffect(() => {
    if (workspace) {
      setWsName(workspace.name || '');
      setWsDesc(workspace.description || '');
      setWsGoal(workspace.goal || '');
      setWsSuccessMetrics(workspace.success_metrics || '');
      setWsDecisionPoints(workspace.decision_points || '');
    }
  }, [workspace]);

  // Rules fields
  const [ruleName, setRuleName] = useState('');
  const [ruleType, setRuleType] = useState('threshold');
  const [rulePriority, setRulePriority] = useState(1);
  const [ruleDetails, setRuleDetails] = useState('');

  useEffect(() => {
    if (workspace?.id) {
      loadRules();
    }
  }, [workspace?.id]);

  const loadRules = async () => {
    setLoading(true);
    try {
      const fetched = await api.getRules(workspace.id);
      setRules(fetched);
    } catch (err) {
      toast.error('Failed to load rules.');
    }
    setLoading(false);
  };

  const handleUpdateWorkspace = async (e) => {
    e.preventDefault();
    setIsSavingWs(true);
    try {
      const payload = {
        ...workspace,
        name: wsName,
        description: wsDesc,
        goal: wsGoal,
        success_metrics: wsSuccessMetrics,
        decision_points: wsDecisionPoints
      };
      const updated = await api.updateWorkspace(workspace.id, payload);
      if (setWorkspaces) {
        setWorkspaces(prev => prev.map(w => w.id === updated.id ? updated : w));
      }
      toast.success('Workspace updated successfully!');
    } catch (err) {
      toast.error('Failed to update workspace.');
    }
    setIsSavingWs(false);
  };

  const handleAddRule = async (e) => {
    e.preventDefault();
    if (!ruleName.trim()) return;

    try {
      const orgId = user.organization_ids?.[0];
      await api.createRule(workspace.id, orgId, {
        name: ruleName,
        type: ruleType,
        priority: parseInt(rulePriority),
        details: ruleDetails
      });

      setRuleName('');
      setRuleDetails('');
      toast.success('Rule created successfully!');
      loadRules();
    } catch (err) {
      toast.error('Failed to create rule.');
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      await api.deleteRule(workspace.id, ruleId);
      toast.success('Rule deleted successfully!');
      loadRules();
    } catch (err) {
      toast.error('Failed to delete rule.');
    }
  };

  return (
    <div className="full-page-scroll">
      <div className="org-hub-welcome">
        <h1>Settings</h1>
        <p>Manage your user account, workspace business rules, and tenant preferences.</p>
      </div>

      <div className="settings-container">
        {/* Left tabs */}
        <div className="settings-nav">
          <button className={`settings-nav-btn ${activePane === 'workspace' ? 'active' : ''}`} onClick={() => setActivePane('workspace')}>
            Workspace Details
          </button>
          <button className={`settings-nav-btn ${activePane === 'rules' ? 'active' : ''}`} onClick={() => setActivePane('rules')}>
            Workspace Rules
          </button>
        </div>

        {/* Right pane content */}
        <div className="settings-pane">
          {activePane === 'rules' && (
            <div>
              <h2>Workspace Rules</h2>
              <p className="subtitle">Define mandatory rules, constraints, and priorities that the AI evaluates against candidates.</p>

              <div style={{ display: 'flex', gap: '32px' }}>
                {/* Active Rules List */}
                <div style={{ flex: 1.5 }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px' }}>Active Business Rules</h3>
                  <div className="rules-manager-list">
                    {rules.map((rule) => (
                      <div key={rule.id} className="rule-manager-card">
                        <div className="rule-manager-left">
                          <h4>{rule.name}</h4>
                          <p className="details">{rule.description}</p>
                        </div>
                        <div className="rule-manager-right">
                          <span className="workspace-status-badge active" style={{ fontSize: '10px' }}>
                            Priority {rule.priority}
                          </span>
                          <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => handleDeleteRule(rule.id)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                    {rules.length === 0 && (
                      <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>No custom rules registered in this workspace yet.</div>
                    )}
                  </div>
                </div>

                {/* Add Rule Form */}
                <div style={{ flex: 1, backgroundColor: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px', height: 'fit-content' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <PlusCircle size={16} style={{ color: 'var(--primary)' }} /> Add Rule
                  </h3>

                  <form onSubmit={handleAddRule} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="form-group">
                      <label>Rule Name</label>
                      <input type="text" placeholder="e.g. Budget Constraint" value={ruleName} onChange={e => setRuleName(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label>Evaluation Type</label>
                      <select value={ruleType} onChange={e => setRuleType(e.target.value)}>
                        <option value="threshold">Numerical Threshold</option>
                        <option value="hard_filter">Hard Filter Check</option>
                        <option value="mandatory_field">Field Presence</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Priority Rank</label>
                      <input type="number" min="1" max="100" value={rulePriority} onChange={e => setRulePriority(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label>Check Condition Details</label>
                      <input type="text" placeholder="e.g. Annual Cost <= 150000" value={ruleDetails} onChange={e => setRuleDetails(e.target.value)} required />
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ padding: '8px' }}>
                      Register Rule
                    </button>
                  </form>
                </div>
              </div>
            </div>
          )}

          {activePane === 'workspace' && (
            <div>
              <h2>Workspace Details</h2>
              <p className="subtitle">Update the core details, goal, success metrics, and decision points for this workspace.</p>

              <form onSubmit={handleUpdateWorkspace} className="settings-form">
                <div className="form-group">
                  <label>Workspace Name</label>
                  <input type="text" value={wsName} onChange={e => setWsName(e.target.value)} placeholder="e.g. Sales Optimization Operations" required />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea 
                    value={wsDesc} 
                    onChange={e => setWsDesc(e.target.value)} 
                    placeholder="Describe the workspace purpose..." 
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', height: '80px', resize: 'none', outline: 'none' }}
                  />
                </div>
                <div className="form-group">
                  <label>Goal</label>
                  <input type="text" value={wsGoal} onChange={e => setWsGoal(e.target.value)} placeholder="e.g. Select the best CRM" />
                </div>
                <div className="form-group">
                  <label>Success Metrics</label>
                  <input type="text" value={wsSuccessMetrics} onChange={e => setWsSuccessMetrics(e.target.value)} placeholder="e.g. High user adoption, under budget" />
                </div>
                <div className="form-group">
                  <label>Decision Points</label>
                  <input type="text" value={wsDecisionPoints} onChange={e => setWsDecisionPoints(e.target.value)} placeholder="e.g. Cost, Integration, Support" />
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: 'fit-content', marginTop: '12px' }} disabled={isSavingWs}>
                  {isSavingWs ? 'Saving...' : 'Save Workspace Details'}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
