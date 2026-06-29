import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedLayout from './components/ProtectedLayout';
import Login from './views/Login';
import MainHome from './views/MainHome';
import Knowledge from './views/Knowledge';
import Decisions from './views/Decisions';
import Review from './views/Review';
import History from './views/History';
import Settings from './views/Settings';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-main)' }}>
        <LoaderSpinner size={32} />
        <p style={{ marginTop: '16px', color: 'var(--text-muted)', fontWeight: 600 }}>Initializing DecisiolQ Dashboard...</p>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster position="top-right" richColors />
        <Routes>
          <Route path="/login" element={<LoginWrapper />} />
          
          <Route path="/" element={<ProtectedRoute><ProtectedLayout /></ProtectedRoute>}>
            <Route index element={<MainHomeWrapper />} />
            
            <Route path="workspaces/:workspaceId">
              <Route index element={<DecisionsWrapper />} />
              <Route path="decisions/:decisionId" element={<ReviewWrapper />} />
              <Route path="knowledge" element={<KnowledgeWrapper />} />
              <Route path="history" element={<HistoryWrapper />} />
              <Route path="settings" element={<SettingsWrapper />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

// Simple wrappers to adapt existing components that expected direct props
import { useOutletContext, useParams, useNavigate } from 'react-router-dom';

function LoginWrapper() {
  const { user } = useAuth();
  if (user) {
    return <Navigate to="/" replace />;
  }
  return <Login />;
}

function MainHomeWrapper() {
  const { user, setShowGlobalUploadWizard } = useOutletContext();
  const navigate = useNavigate();
  return (
    <MainHome 
      user={user} 
      onSelectWorkspace={(ws) => navigate(`/workspaces/${ws.id}`)}
      onTriggerUpload={() => setShowGlobalUploadWizard(true)} 
    />
  );
}

function DecisionsWrapper() {
  const { activeWorkspace } = useOutletContext();
  const navigate = useNavigate();
  if (!activeWorkspace) return null;
  return (
    <Decisions 
      workspace={activeWorkspace} 
      initialQuery=""
      onDecisionComplete={(id) => navigate(`/workspaces/${activeWorkspace.id}/decisions/${id}`)}
    />
  );
}

function ReviewWrapper() {
  const { activeWorkspace } = useOutletContext();
  const { decisionId } = useParams();
  const navigate = useNavigate();
  if (!activeWorkspace) return null;
  return (
    <Review 
      workspace={activeWorkspace} 
      decisionId={decisionId}
      onBackToDashboard={() => navigate(`/workspaces/${activeWorkspace.id}`)}
      onViewDetails={() => alert('Reloading real-time trace details graph...')}
    />
  );
}

function KnowledgeWrapper() {
  const { activeWorkspace, user, setWorkspaces } = useOutletContext();
  if (!activeWorkspace) return null;
  return (
    <Knowledge 
      workspace={activeWorkspace} 
      user={user}
      onUpdateWorkspace={(updatedWs) => {
        setWorkspaces(prev => prev.map(w => w.id === updatedWs.id ? updatedWs : w));
      }}
    />
  );
}

function HistoryWrapper() {
  const { activeWorkspace } = useOutletContext();
  if (!activeWorkspace) return null;
  return <History workspace={activeWorkspace} />;
}

function SettingsWrapper() {
  const { activeWorkspace, user, setWorkspaces } = useOutletContext();
  if (!activeWorkspace) return null;
  return <Settings workspace={activeWorkspace} user={user} setWorkspaces={setWorkspaces} />;
}

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
