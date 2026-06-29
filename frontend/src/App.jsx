import React, { useState, useEffect } from 'react';
import { Layers, HelpCircle, LogOut, ChevronDown, Check, Plus, Bell, Search, Info, CloudLightning } from 'lucide-react';
import { api, clearTokens } from './services/api';
import Login from './views/Login';
import MainHome from './views/MainHome';
import Knowledge from './views/Knowledge';
import Decisions from './views/Decisions';
import Review from './views/Review';
import History from './views/History';
import Settings from './views/Settings';
import UploadWizard from './components/UploadWizard';

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [currentTab, setCurrentTab] = useState('home'); // 'home' | 'knowledge' | 'history' | 'settings'
  const [workspaces, setWorkspaces] = useState([]);
  const [showWorkspaceDropdown, setShowWorkspaceDropdown] = useState(false);
  const [triggerUpload, setTriggerUpload] = useState(false);
  const [showGlobalUploadWizard, setShowGlobalUploadWizard] = useState(false);

  // Decisions Flow Subviews
  const [decisionTab, setDecisionTab] = useState('input'); // 'input' | 'graph' | 'review'
  const [activeDecisionId, setActiveDecisionId] = useState(null);
  const [initialDecisionQuery, setInitialDecisionQuery] = useState('');

  // Main dropdown modals
  const [showCreateWsModal, setShowCreateWsModal] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [newWsDesc, setNewWsDesc] = useState('');

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    const currentUser = await api.getMe();
    if (currentUser) {
      setUser(currentUser);
      loadWorkspaces(currentUser.organization_ids?.[0]);
    }
    setLoading(false);
  };

  const loadWorkspaces = async (orgId) => {
    if (!orgId) return;
    const fetched = await api.getWorkspaces(orgId);
    setWorkspaces(fetched);
  };

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    loadWorkspaces(loggedInUser.organization_ids?.[0]);
    setActiveWorkspace(null); // start on main home
  };

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    setActiveWorkspace(null);
    setWorkspaces([]);
  };

  const handleSelectWorkspace = (ws) => {
    setActiveWorkspace(ws);
    setCurrentTab('home');
    setDecisionTab('input');
    setActiveDecisionId(null);
    setInitialDecisionQuery('');
    setShowWorkspaceDropdown(false);
  };

  const handleNavigateTab = (tab, query = '') => {
    setCurrentTab(tab);
    if (tab === 'home') {
      setDecisionTab('input');
      setActiveDecisionId(null);
      setInitialDecisionQuery(query);
    }
  };

  const handleDecisionComplete = (id) => {
    setActiveDecisionId(id);
    setDecisionTab('review');
  };

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!newWsName.trim()) return;

    const orgId = user.organization_ids?.[0];
    const newWs = await api.createWorkspace(orgId, newWsName, newWsDesc, user.id);
    setNewWsName('');
    setNewWsDesc('');
    setShowCreateWsModal(false);

    // Refresh workspaces and select the newly created one
    const fetched = await api.getWorkspaces(orgId);
    setWorkspaces(fetched);
    handleSelectWorkspace(newWs);
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-main)' }}>
        <LoaderSpinner size={32} />
        <p style={{ marginTop: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Initializing DecisiolQ Dashboard...</p>
      </div>
    );
  }

  // Not Logged In
  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app-container" style={{ flexDirection: 'column' }}>
      {/* Universal Top Navbar */}
      <nav className="navbar">
        <div className="navbar-brand-section">
          <a href="#home" className="navbar-brand-logo" onClick={(e) => { e.preventDefault(); setActiveWorkspace(null); }}>
            <div className="navbar-logo-icon">IQ</div>
            <span>DecisiolQ</span>
          </a>

          {/* Active Workspace Selector Dropdown */}
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
                  onClick={() => { setActiveWorkspace(null); setShowWorkspaceDropdown(false); }}
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
                <div className="dropdown-create-btn" onClick={() => { setShowWorkspaceDropdown(false); setShowCreateWsModal(true); }}>
                  <Plus size={14} />
                  <span>Create Workspace</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Global Search Bar */}
        {/* <div className="navbar-search">
          <Search size={16} className="navbar-search-icon" />
          <input type="text" placeholder="Search knowledge assets, decisions, rules..." />
          <span className="navbar-search-shortcut">⌘ K</span>
        </div> */}

        {/* Top-Right Profile / Actions */}
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
            <span className="navbar-user-name">{user.full_name || 'Alex Johnson'}</span>
            <LogOut size={16} style={{ color: 'var(--text-muted)', marginLeft: '4px' }} />
          </div>
        </div>
      </nav>

      {/* Main Body Section */}
      <div className="app-container" style={{ flex: 1, minHeight: 'calc(100vh - var(--navbar-height))' }}>
        {/* Render Left Sidebar only when a workspace is active */}
        {activeWorkspace && (
          <aside className="sidebar">
            <div className="sidebar-menu">
              <button
                className={`sidebar-link ${currentTab === 'home' ? 'active' : ''}`}
                onClick={() => handleNavigateTab('home')}
              >
                <Layers size={18} />
                <span>Home</span>
              </button>
              <button
                className={`sidebar-link ${currentTab === 'knowledge' ? 'active' : ''}`}
                onClick={() => handleNavigateTab('knowledge')}
              >
                <Layers size={18} />
                <span>Knowledge</span>
              </button>
              <button
                className={`sidebar-link ${currentTab === 'history' ? 'active' : ''}`}
                onClick={() => handleNavigateTab('history')}
              >
                <Layers size={18} />
                <span>History</span>
              </button>
              <button
                className={`sidebar-link ${currentTab === 'settings' ? 'active' : ''}`}
                onClick={() => handleNavigateTab('settings')}
              >
                <Layers size={18} />
                <span>Settings</span>
              </button>
            </div>

            {/* Bottom Upgrade Widget */}
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

        {/* Central Display Pane */}
        <main className="main-content">
          {!activeWorkspace ? (
            /* Organization Overview page (No Sidebar) */
            <MainHome
              user={user}
              onSelectWorkspace={handleSelectWorkspace}
              onTriggerUpload={() => {
                setShowGlobalUploadWizard(true);
              }}
            />
          ) : (
            /* Active Workspace Subpages */
            <>
              {currentTab === 'home' && (
                <>
                  {decisionTab === 'input' && (
                    <Decisions
                      workspace={activeWorkspace}
                      initialQuery={initialDecisionQuery}
                      onDecisionComplete={handleDecisionComplete}
                    />
                  )}
                  {decisionTab === 'review' && (
                    <Review
                      workspace={activeWorkspace}
                      decisionId={activeDecisionId}
                      onBackToDashboard={() => {
                        setDecisionTab('input');
                        setActiveDecisionId(null);
                        setInitialDecisionQuery('');
                      }}
                      onViewDetails={() => {
                        // view flow details
                        alert('Reloading real-time trace details graph...');
                        setDecisionTab('input');
                        setInitialDecisionQuery('Recommend the best software vendor for our AI infrastructure.');
                      }}
                    />
                  )}
                </>
              )}

              {currentTab === 'knowledge' && (
                <Knowledge
                  workspace={activeWorkspace}
                  user={user}
                  onUpdateWorkspace={(updatedWs) => {
                    setActiveWorkspace(updatedWs);
                    setWorkspaces(prev => prev.map(w => w.id === updatedWs.id ? updatedWs : w));
                  }}
                />
              )}

              {currentTab === 'history' && (
                <History workspace={activeWorkspace} />
              )}

              {currentTab === 'settings' && (
                <Settings workspace={activeWorkspace} user={user} />
              )}
            </>
          )}
        </main>
      </div>

      {/* Global Navbar Switcher Create Workspace Modal */}
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
                <div className="auth-input-group">
                  <label>Description</label>
                  <textarea
                    style={{ padding: '10px 14px', border: '1px solid var(--border)', borderRadius: '6px', width: '100%', height: '100px', resize: 'none', outline: 'none' }}
                    placeholder="Describe the workspace purpose..."
                    value={newWsDesc}
                    onChange={(e) => setNewWsDesc(e.target.value)}
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
          onSuccess={(newAsset) => {
            setShowGlobalUploadWizard(false);
            alert('Document uploaded globally successfully!');
          }}
        />
      )}
    </div>
  );
}

// Simple loader icon component
function LoaderSpinner({ size = 24 }) {
  return (
    <svg
      className="inspector-agent-avatar running"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="var(--primary)"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
