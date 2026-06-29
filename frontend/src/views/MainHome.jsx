import React, { useState, useEffect } from 'react';
import { Layers, CheckSquare, BookOpen, Users, UploadCloud, PlusCircle, ArrowRight, FolderPlus } from 'lucide-react';
import { api } from '../services/api';
import { toast } from 'sonner';

export default function MainHome({ user, onSelectWorkspace, onTriggerUpload }) {
  const [stats, setStats] = useState({ total_workspaces: 0, decisions_made: 0, knowledge_assets: 0, active_users: 0 });
  const [workspaces, setWorkspaces] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [newWsDesc, setNewWsDesc] = useState('');
  const [newWsGoal, setNewWsGoal] = useState('');
  const [newWsSuccessMetrics, setNewWsSuccessMetrics] = useState('');
  const [newWsDecisionPoints, setNewWsDecisionPoints] = useState('');
  const [loading, setLoading] = useState(false);

  const orgId = user.organization_ids?.[0];

  useEffect(() => {
    if (orgId) {
      loadDashboardData();
    }
  }, [orgId]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const fetchedStats = await api.getOrgStats(orgId);
      const fetchedWorkspaces = await api.getWorkspaces(orgId);
      setStats(fetchedStats);
      setWorkspaces(fetchedWorkspaces);
    } catch (err) {
      toast.error('Failed to load dashboard data. Please try again.');
    }
    setLoading(false);
  };

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!orgId) {
      toast.error('Onboarding Prerequisite: You must be assigned to an organization to create a workspace.');
      setShowCreateModal(false);
      return;
    }
    if (!newWsName.trim()) return;

    try {
      await api.createWorkspace(newWsName, newWsDesc, newWsGoal, newWsSuccessMetrics, newWsDecisionPoints);
      setNewWsName('');
      setNewWsDesc('');
      setNewWsGoal('');
      setNewWsSuccessMetrics('');
      setNewWsDecisionPoints('');
      setShowCreateModal(false);
      toast.success('Workspace created successfully!');
      loadDashboardData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create workspace.');
    }
  };

  return (
    <div className="full-page-scroll">
      {/* Welcome Section */}
      <div className="org-hub-welcome">
        <h1>Welcome back, {user.full_name || 'Alex'}! 👋</h1>
        <p>Here's what's happening across your organization today.</p>
      </div>

      {/* Stats Counter Grid */}
      <div className="stats-grid">
        <div className="stats-card">
          <div className="stats-card-header">
            <div className="stats-card-icon"><Layers size={20} /></div>
          </div>
          <h3>{stats.total_workspaces}</h3>
          <p>Total Workspaces</p>
          <a href="#workspaces" className="stats-card-footer-link" onClick={(e) => e.preventDefault()}>
            <span>View Home</span>
            <ArrowRight size={14} />
          </a>
        </div>

        <div className="stats-card">
          <div className="stats-card-header">
            <div className="stats-card-icon" style={{ color: 'var(--success)' }}><CheckSquare size={20} /></div>
          </div>
          <h3>{stats.decisions_made}</h3>
          <p>Decisions Made</p>
          <a href="#decisions" className="stats-card-footer-link" onClick={(e) => e.preventDefault()}>
            <span>View all decisions</span>
            <ArrowRight size={14} />
          </a>
        </div>

        <div className="stats-card">
          <div className="stats-card-header">
            <div className="stats-card-icon" style={{ color: '#7c3aed' }}><BookOpen size={20} /></div>
          </div>
          <h3>{stats.knowledge_assets.toLocaleString()}</h3>
          <p>Knowledge Assets</p>
          <a href="#knowledge" className="stats-card-footer-link" onClick={(e) => e.preventDefault()}>
            <span>View knowledge</span>
            <ArrowRight size={14} />
          </a>
        </div>

        <div className="stats-card">
          <div className="stats-card-header">
            <div className="stats-card-icon" style={{ color: '#f59e0b' }}><Users size={20} /></div>
          </div>
          <h3>{stats.active_users}</h3>
          <p>Active Users</p>
          <a href="#users" className="stats-card-footer-link" onClick={(e) => e.preventDefault()}>
            <span>View all users</span>
            <ArrowRight size={14} />
          </a>
        </div>
      </div>

      {/* Action Banner Cards */}
      <div className="action-banners-grid">
        <div className="action-banner-card" onClick={onTriggerUpload}>
          <div className="action-banner-left">
            <div className="action-banner-icon"><UploadCloud size={24} /></div>
            <div className="action-banner-text">
              <h3>Upload Knowledge</h3>
              <p>Add documents, policies, data sources</p>
            </div>
          </div>
          <ArrowRight className="action-banner-arrow" size={20} />
        </div>

        <div className="action-banner-card" onClick={() => onSelectWorkspace(workspaces[0])}>
          <div className="action-banner-left">
            <div className="action-banner-icon" style={{ color: 'var(--primary)', backgroundColor: 'var(--primary-light)' }}><PlusCircle size={24} /></div>
            <div className="action-banner-text">
              <h3>Start New Decision</h3>
              <p>Create a new decision request</p>
            </div>
          </div>
          <ArrowRight className="action-banner-arrow" size={20} />
        </div>
      </div>

      {/* Workspace List Table */}
      <div>
        <div className="table-section-header">
          <h2>Home</h2>
          <button className="btn btn-secondary" onClick={() => {
            if (!orgId) {
              toast.error('Onboarding Prerequisite: You must be assigned to an organization to create a workspace.');
            } else {
              setShowCreateModal(true);
            }
          }}>
            <PlusCircle size={16} />
            <span>Create Workspace</span>
          </button>
        </div>

        <div className="table-container">
          <table className="app-table">
            <thead>
              <tr>
                <th style={{ width: '25%' }}>Workspace</th>
                <th style={{ width: '30%' }}>Description</th>
                <th>Decisions (30d)</th>
                <th>Knowledge Assets</th>
                <th>Active Users</th>
                <th>Status</th>
                <th>Last Activity</th>
                <th style={{ width: '4%' }}></th>
              </tr>
            </thead>
            <tbody>
              {workspaces.map((ws) => (
                <tr key={ws.id} onClick={() => onSelectWorkspace(ws)}>
                  <td>
                    <div className="workspace-cell-name">
                      <div className="workspace-avatar">
                        {ws.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()}
                      </div>
                      <span>{ws.name}</span>
                    </div>
                  </td>
                  <td>{ws.description}</td>
                  <td>{ws.decisions_count_30d || 0}</td>
                  <td>{ws.knowledge_assets_count || 0}</td>
                  <td>{ws.active_users_count || 0}</td>
                  <td>
                    <span className="workspace-status-badge active">
                      {ws.status || 'Active'}
                    </span>
                  </td>
                  <td>{ws.last_activity}</td>
                  <td className="table-action-cell">
                    <ArrowRight size={16} className="table-action-icon" style={{ color: 'var(--primary)' }} />
                  </td>
                </tr>
              ))}
              {workspaces.length === 0 && (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '32px' }}>
                    No workspaces found. Click "Create Workspace" to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create a New Workspace</h3>
              <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setShowCreateModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateWorkspace}>
              <div className="modal-body">
                <div className="auth-input-group" style={{ marginBottom: '20px' }}>
                  <label>Workspace Name</label>
                  <input
                    type="text"
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', outline: 'none' }}
                    placeholder="e.g. CRM Software Vendor Evaluation"
                    value={newWsName}
                    onChange={(e) => setNewWsName(e.target.value)}
                    required
                  />
                </div>
                <div className="auth-input-group" style={{ marginBottom: '20px' }}>
                  <label>Description</label>
                  <textarea
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', height: '80px', resize: 'none', outline: 'none' }}
                    placeholder="Describe the purpose of this workspace..."
                    value={newWsDesc}
                    onChange={(e) => setNewWsDesc(e.target.value)}
                  />
                </div>
                <div className="auth-input-group" style={{ marginBottom: '20px' }}>
                  <label>Goal</label>
                  <input
                    type="text"
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', outline: 'none' }}
                    placeholder="e.g. Select the best CRM"
                    value={newWsGoal}
                    onChange={(e) => setNewWsGoal(e.target.value)}
                  />
                </div>
                <div className="auth-input-group" style={{ marginBottom: '20px' }}>
                  <label>Success Metrics</label>
                  <input
                    type="text"
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', outline: 'none' }}
                    placeholder="e.g. High user adoption, under budget"
                    value={newWsSuccessMetrics}
                    onChange={(e) => setNewWsSuccessMetrics(e.target.value)}
                  />
                </div>
                <div className="auth-input-group">
                  <label>Decision Points</label>
                  <input
                    type="text"
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', outline: 'none' }}
                    placeholder="e.g. Cost, Integration, Support"
                    value={newWsDecisionPoints}
                    onChange={(e) => setNewWsDecisionPoints(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Workspace</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
