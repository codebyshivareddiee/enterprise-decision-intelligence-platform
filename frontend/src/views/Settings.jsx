import React, { useState, useEffect } from 'react';
import { Shield, PlusCircle, AlertCircle, Trash2, Key, Users, Settings as SettingsIcon } from 'lucide-react';
import { api } from '../services/api';
import { toast } from 'sonner';

export default function Settings({ workspace, user }) {
  const [activePane, setActivePane] = useState('profile');
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(false);

  // Profile fields
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

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

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    if (!oldPassword || !newPassword) return;
    
    // Simulate change password
    toast.success('Password updated successfully!');
    setOldPassword('');
    setNewPassword('');
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

  return (
    <div className="full-page-scroll">
      <div className="org-hub-welcome">
        <h1>Settings</h1>
        <p>Manage your user account, workspace business rules, and tenant preferences.</p>
      </div>

      <div className="settings-container">
        {/* Left tabs */}
        <div className="settings-nav">
          <button className={`settings-nav-btn ${activePane === 'profile' ? 'active' : ''}`} onClick={() => setActivePane('profile')}>
            User Profile
          </button>
          <button className={`settings-nav-btn ${activePane === 'rules' ? 'active' : ''}`} onClick={() => setActivePane('rules')}>
            Workspace Rules
          </button>
          <button className={`settings-nav-btn ${activePane === 'org' ? 'active' : ''}`} onClick={() => setActivePane('org')}>
            Organization Info
          </button>
        </div>

        {/* Right pane content */}
        <div className="settings-pane">
          {activePane === 'profile' && (
            <div>
              <h2>User Profile</h2>
              <p className="subtitle">Update your profile parameters and security credentials.</p>

              <form onSubmit={handleUpdatePassword} className="settings-form">
                <div className="form-group">
                  <label>Full Name</label>
                  <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Email Address (Disabled)</label>
                  <input type="email" value={user?.email || ''} disabled style={{ backgroundColor: 'var(--bg-main)', cursor: 'not-allowed' }} />
                </div>

                <div style={{ margin: '16px 0', borderTop: '1px solid var(--border)' }}></div>

                <h3 style={{ fontSize: '15px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <Key size={16} /> Change Password
                </h3>

                <div className="form-group">
                  <label>Old Password</label>
                  <input type="password" placeholder="Enter old password" value={oldPassword} onChange={e => setOldPassword(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>New Password</label>
                  <input type="password" placeholder="Enter new password" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: 'fit-content', marginTop: '12px' }}>
                  Save Profile Settings
                </button>
              </form>
            </div>
          )}

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
                          <p className="details">{rule.details}</p>
                        </div>
                        <div className="rule-manager-right">
                          <span className="workspace-status-badge active" style={{ fontSize: '10px' }}>
                            Priority {rule.priority}
                          </span>
                          <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => alert('Rule deletion is mocked.')}>
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

          {activePane === 'org' && (
            <div>
              <h2>Organization Info</h2>
              <p className="subtitle">System details regarding your tenant isolation configuration.</p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '520px' }}>
                <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '6px', backgroundColor: 'var(--bg-main)' }}>
                  <strong style={{ fontSize: '13px', display: 'block', marginBottom: '4px' }}>Acme Corporation</strong>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Tenant Domain Isolation: <code>acme.com</code></p>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Organization ID: <code>{user?.organization_ids?.[0] || 'Unknown'}</code></p>
                </div>

                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <Users size={16} /> User Memberships
                  </h3>
                  <table className="app-table" style={{ fontSize: '12.5px' }}>
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Global Role</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>Alex Johnson (You)</td>
                        <td>ORGANIZATION_ADMIN</td>
                        <td><span className="workspace-status-badge active">Active</span></td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>Priya S.</td>
                        <td>DECISION_REVIEWER</td>
                        <td><span className="workspace-status-badge active">Active</span></td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>Michael T.</td>
                        <td>KNOWLEDGE_MANAGER</td>
                        <td><span className="workspace-status-badge active">Active</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
