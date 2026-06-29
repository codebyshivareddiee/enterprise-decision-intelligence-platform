import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { Layers, HelpCircle, LogOut, ChevronDown, Check, Plus, Bell, CloudLightning } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { toast } from 'sonner';
import UploadWizard from './UploadWizard';

export default function ProtectedLayout() {
  const { user, logout, checkAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [showOrgOnboarding, setShowOrgOnboarding] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgDesc, setNewOrgDesc] = useState('');
  
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [showWorkspaceDropdown, setShowWorkspaceDropdown] = useState(false);
  const [showCreateWsModal, setShowCreateWsModal] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [newWsDesc, setNewWsDesc] = useState('');
  const [newWsGoal, setNewWsGoal] = useState('');
  const [newWsSuccessMetrics, setNewWsSuccessMetrics] = useState('');
  const [newWsDecisionPoints, setNewWsDecisionPoints] = useState('');
  const [showGlobalUploadWizard, setShowGlobalUploadWizard] = useState(false);

  useEffect(() => {
    if (user) {
      if (!user.organization_ids?.length) {
        setShowOrgOnboarding(true);
      } else {
        setShowOrgOnboarding(false);
        loadWorkspaces(user.organization_ids[0]);
      }
    }
  }, [user]);

  const handleCreateOrganization = async (e) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    try {
      await api.createOrganization(newOrgName, newOrgDesc);
      toast.success('Organization created successfully!');
      await checkAuth();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create organization.');
    }
  };

  // Sync active workspace from URL
  useEffect(() => {
    const match = location.pathname.match(/\/workspaces\/([^\/]+)/);
    if (match && workspaces.length > 0) {
      const wsId = match[1];
      const ws = workspaces.find(w => w.id === wsId);
      if (ws) setActiveWorkspace(ws);
    } else if (location.pathname === '/') {
      setActiveWorkspace(null);
    }
  }, [location.pathname, workspaces]);

  const loadWorkspaces = async (orgId) => {
    try {
      const fetched = await api.getWorkspaces(orgId);
      setWorkspaces(fetched);
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSelectWorkspace = (ws) => {
    if (ws) {
      navigate(`/workspaces/${ws.id}`);
    } else {
      navigate('/');
    }
    setShowWorkspaceDropdown(false);
  };

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    const orgId = user?.organization_ids?.[0];
    if (!orgId) {
      toast.error('Onboarding Prerequisite: You must be assigned to an organization to create a workspace.');
      setShowCreateWsModal(false);
      return;
    }
    if (!newWsName.trim()) return;

    try {
      const newWs = await api.createWorkspace(newWsName, newWsDesc, newWsGoal, newWsSuccessMetrics, newWsDecisionPoints);
      setNewWsName('');
      setNewWsDesc('');
      setNewWsGoal('');
      setNewWsSuccessMetrics('');
      setNewWsDecisionPoints('');
      setShowCreateWsModal(false);
      toast.success('Workspace created successfully!');

      const fetched = await api.getWorkspaces(orgId);
      setWorkspaces(fetched);
      handleSelectWorkspace(newWs);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create workspace.');
      console.error(e);
    }
  };

  const currentTab = location.pathname.split('/').pop() || 'home';

  return (
    <div className="app-container" style={{ flexDirection: 'column' }}>
      <nav className="navbar">
        <div className="navbar-brand-section">
          <Link to="/" className="navbar-brand-logo" onClick={() => setActiveWorkspace(null)}>
            <div className="navbar-logo-icon">IQ</div>
            <span>DecisiolQ</span>
          </Link>

          <div className="workspace-switcher">
            <div className="workspace-switcher-trigger" onClick={() => setShowWorkspaceDropdown(!showWorkspaceDropdown)}>
              <div className="workspace-avatar">
                {activeWorkspace ? activeWorkspace.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() : 'AC'}
              </div>
              <span className="navbar-user-name">
                {activeWorkspace ? activeWorkspace.name : 'Home'}
              </span>
              <ChevronDown size={14} className="navbar-btn" style={{ padding: 0 }} />
            </div>

            {showWorkspaceDropdown && (
              <div className="workspace-switcher-dropdown">
                <div className="dropdown-header">Workspaces</div>
                <div
                  className="dropdown-item"
                  onClick={() => handleSelectWorkspace(null)}
                  style={{ fontWeight: !activeWorkspace ? 'bold' : 'normal' }}
                >
                  <div className="dropdown-item-left">
                    <div className="workspace-avatar" style={{ backgroundColor: '#cbd5e1', color: '#475569' }}>ALL</div>
                    <span>Home</span>
                  </div>
                  {!activeWorkspace && <Check size={14} style={{ color: 'var(--primary)' }} />}
                </div>

                <div className="dropdown-divider"></div>

                {workspaces.map(ws => (
                  <div
                    key={ws.id}
                    className="dropdown-item"
                    onClick={() => handleSelectWorkspace(ws)}
                    style={{ fontWeight: activeWorkspace?.id === ws.id ? 'bold' : 'normal' }}
                  >
                    <div className="dropdown-item-left">
                      <div className="workspace-avatar">
                        {ws.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()}
                      </div>
                      <span>{ws.name}</span>
                    </div>
                    {activeWorkspace?.id === ws.id && <Check size={14} style={{ color: 'var(--primary)' }} />}
                  </div>
                ))}

                <div className="dropdown-divider"></div>
                <div className="dropdown-create-btn" onClick={() => { 
                  setShowWorkspaceDropdown(false); 
                  if (!user?.organization_ids?.[0]) {
                    toast.error('Onboarding Prerequisite: You must be assigned to an organization to create a workspace.');
                  } else {
                    setShowCreateWsModal(true); 
                  }
                }}>
                  <Plus size={14} />
                  <span>Create Workspace</span>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="navbar-actions">
          <button className="navbar-btn" title="Help">
            <HelpCircle size={18} />
          </button>
          <button className="navbar-btn" title="Notifications">
            <Bell size={18} />
            <div className="navbar-badge"></div>
          </button>
          <div className="dropdown-divider" style={{ width: '1px', height: '24px', margin: 0 }}></div>
          <div className="navbar-user-menu" onClick={handleLogout} title="Log Out">
            <img
              className="navbar-user-avatar"
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=256&auto=format&fit=crop"
              alt="Avatar"
            />
            <span className="navbar-user-name">{user?.full_name || 'User'}</span>
            <LogOut size={16} style={{ color: 'var(--text-muted)', marginLeft: '4px' }} />
          </div>
        </div>
      </nav>

      <div className="app-container" style={{ flex: 1, minHeight: 'calc(100vh - var(--navbar-height))' }}>
        {activeWorkspace && (
          <aside className="sidebar">
            <div className="sidebar-menu">
              <Link to={`/workspaces/${activeWorkspace.id}`} className={`sidebar-link ${location.pathname === `/workspaces/${activeWorkspace.id}` || location.pathname.includes('/decisions') ? 'active' : ''}`}>
                <Layers size={18} />
                <span>Home</span>
              </Link>
              <Link to={`/workspaces/${activeWorkspace.id}/knowledge`} className={`sidebar-link ${currentTab === 'knowledge' ? 'active' : ''}`}>
                <Layers size={18} />
                <span>Knowledge</span>
              </Link>
              <Link to={`/workspaces/${activeWorkspace.id}/history`} className={`sidebar-link ${currentTab === 'history' ? 'active' : ''}`}>
                <Layers size={18} />
                <span>History</span>
              </Link>
              <Link to={`/workspaces/${activeWorkspace.id}/settings`} className={`sidebar-link ${currentTab === 'settings' ? 'active' : ''}`}>
                <Layers size={18} />
                <span>Settings</span>
              </Link>
            </div>
            <div className="sidebar-footer-card">
              <div className="sidebar-footer-stats">
                <CloudLightning size={16} style={{ color: 'var(--primary)' }} />
                <div className="sidebar-footer-text">
                  <h4>Storage</h4>
                  <p>12.4 GB of 100 GB used</p>
                </div>
              </div>
              <div className="sidebar-progress-bar">
                <div className="sidebar-progress-fill" style={{ width: '12.4%' }}></div>
              </div>
              <button className="sidebar-footer-btn" onClick={() => alert('Storage upgrade panel is mocked.')}>
                Upgrade
              </button>
            </div>
          </aside>
        )}

        <main className="main-content">
          <Outlet context={{ activeWorkspace, user, setWorkspaces, setShowGlobalUploadWizard }} />
        </main>
      </div>

      {showCreateWsModal && (
        <div className="modal-overlay" onClick={() => setShowCreateWsModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create a New Workspace</h3>
              <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setShowCreateWsModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateWorkspace}>
              <div className="modal-body">
                <div className="auth-input-group" style={{ marginBottom: '20px' }}>
                  <label>Workspace Name</label>
                  <input
                    type="text"
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', outline: 'none' }}
                    placeholder="e.g. Sales Optimization Operations"
                    value={newWsName}
                    onChange={(e) => setNewWsName(e.target.value)}
                    required
                  />
                </div>
                <div className="auth-input-group" style={{ marginBottom: '20px' }}>
                  <label>Description</label>
                  <textarea
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', height: '80px', resize: 'none', outline: 'none' }}
                    placeholder="Describe the workspace purpose..."
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
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateWsModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Workspace</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showGlobalUploadWizard && (
        <UploadWizard
          user={user}
          workspace={null}
          onClose={() => setShowGlobalUploadWizard(false)}
          onSuccess={() => {
            setShowGlobalUploadWizard(false);
            alert('Document uploaded globally successfully!');
          }}
        />
      )}

      {showOrgOnboarding && (
        <div className="modal-overlay" style={{ zIndex: 9999, backdropFilter: 'blur(10px)', backgroundColor: 'rgba(0,0,0,0.6)' }}>
          <div className="modal-card">
            <div className="modal-header">
              <h3>Welcome to DecisiolQ!</h3>
            </div>
            <form onSubmit={handleCreateOrganization}>
              <div className="modal-body">
                <p style={{ color: 'var(--text-muted)', marginBottom: '24px', lineHeight: 1.5 }}>
                  Before you can start creating workspaces, you need to set up your organization. 
                  You will automatically become the Organization Admin.
                </p>
                <div className="auth-input-group" style={{ marginBottom: '20px' }}>
                  <label>Organization Name *</label>
                  <input
                    type="text"
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', outline: 'none' }}
                    placeholder="e.g. Acme Corp"
                    value={newOrgName}
                    onChange={(e) => setNewOrgName(e.target.value)}
                    required
                  />
                </div>
                <div className="auth-input-group">
                  <label>Description (Optional)</label>
                  <textarea
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', height: '80px', resize: 'none', outline: 'none' }}
                    placeholder="Briefly describe your organization..."
                    value={newOrgDesc}
                    onChange={(e) => setNewOrgDesc(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-footer" style={{ justifyContent: 'flex-end' }}>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Create Organization & Continue</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
