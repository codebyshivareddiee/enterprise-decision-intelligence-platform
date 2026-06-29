import React, { useState, useEffect } from 'react';
import { FileText, Plus, Check, X, Cpu, Layers, HelpCircle } from 'lucide-react';
import { api } from '../services/api';
import { toast } from 'sonner';

export default function Knowledge({ workspace, user, onUpdateWorkspace }) {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [activeDrawerTab, setActiveDrawerTab] = useState('details');
  const [showImportModal, setShowImportModal] = useState(false);
  const [selectedImportAssetIds, setSelectedImportAssetIds] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filter States
  const [filterDoc, setFilterDoc] = useState('all');
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    loadKnowledgeAssets();
  }, [workspace?.id]);

  const loadKnowledgeAssets = async () => {
    setLoading(true);
    try {
      const fetchedAssets = await api.getKnowledgeAssets();
      setAssets(fetchedAssets);
      
      // Select first workspace asset by default if it exists
      const wsAssets = workspace
        ? fetchedAssets.filter(asset => workspace.selected_knowledge_asset_ids?.includes(asset.id))
        : [];
        
      if (wsAssets.length > 0) {
        setSelectedAsset(wsAssets[0]);
      } else {
        setSelectedAsset(null);
      }
    } catch (err) {
      toast.error('Failed to load knowledge assets.');
    }
    setLoading(false);
  };

  const handleImportAssets = async () => {
    if (selectedImportAssetIds.length === 0) return;
    
    try {
      const updatedWorkspace = await api.importKnowledgeToWorkspace(workspace.id, selectedImportAssetIds);
      
      if (updatedWorkspace) {
        if (onUpdateWorkspace) {
          onUpdateWorkspace(updatedWorkspace);
        }
        setShowImportModal(false);
        const importedCount = selectedImportAssetIds.length;
        setSelectedImportAssetIds([]);
        toast.success(`${importedCount} knowledge asset${importedCount === 1 ? '' : 's'} imported successfully.`);
        
        // Auto-select the first imported asset if nothing was selected before
        const wsAssets = assets.filter(asset => updatedWorkspace.selected_knowledge_asset_ids?.includes(asset.id));
        if (wsAssets.length > 0 && !selectedAsset) {
          setSelectedAsset(wsAssets[0]);
        }
      }
    } catch (err) {
      toast.error(err.response?.data?.message || err.response?.data?.detail || 'Failed to import documents.');
    }
  };

  // Derive workspace-specific assets
  const workspaceAssets = workspace
    ? assets.filter(asset => workspace.selected_knowledge_asset_ids?.includes(asset.id))
    : [];

  // Apply filters
  const filteredWorkspaceAssets = workspaceAssets.filter(asset => {
    if (filterDoc !== 'all') {
      if (filterDoc === 'pdf' && asset.content_type !== 'pdf') return false;
      if (filterDoc === 'text' && asset.content_type !== 'text') return false;
    }
    if (filterType !== 'all') {
      if (filterType === 'schemas' && !asset.processing_metadata?.schema_selected) return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flex: 1, width: '100%' }}>
      {/* Scrollable grid area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
        <div className="knowledge-header-row">
          <div className="knowledge-header-left">
            <h1>Knowledge</h1>
            <p>Manage and organize your organization's knowledge assets.</p>
          </div>
          <div className="knowledge-actions-wrapper">
            <button className="btn btn-primary" onClick={() => { setSelectedImportAssetIds([]); setShowImportModal(true); }}>
              <Plus size={16} />
              <span>Import Document</span>
            </button>
          </div>
        </div>

        {/* Filter bar */}
        <div className="filter-bar">
          <select className="filter-select" value={filterDoc} onChange={e => setFilterDoc(e.target.value)}>
            <option value="all">All Documents</option>
            <option value="pdf">PDFs only</option>
            <option value="text">Texts only</option>
          </select>
          <select className="filter-select" value={filterType} onChange={e => setFilterType(e.target.value)}>
            <option value="all">All Types</option>
            <option value="schemas">Schemas only</option>
          </select>
        </div>

        {/* Grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>Loading knowledge assets...</div>
        ) : (
          <>
            <div className="knowledge-grid">
              {filteredWorkspaceAssets.map((asset) => {
                const meta = asset.processing_metadata || {};
                const isSelected = selectedAsset?.id === asset.id;
                return (
                  <div
                    key={asset.id}
                    className={`knowledge-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedAsset(asset)}
                  >
                    {isSelected && (
                      <div className="knowledge-card-check">
                        <Check size={12} strokeWidth={3} />
                      </div>
                    )}
                    <div className="knowledge-card-header">
                      <div className="knowledge-file-icon">
                        <FileText size={22} />
                      </div>
                    </div>
                    <h4>{asset.name}</h4>
                    <p className="meta">{asset.size || '1.2 MB'} • Uploaded {asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'recently'}</p>

                    <div className="knowledge-card-pills">
                      <div className="card-pill chunking">
                        <Layers size={12} />
                        <span>{meta.chunking_strategy || 'Default Chunker'}</span>
                      </div>
                      <div className="card-pill analyzer">
                        <Cpu size={12} />
                        <span>{meta.selection_method || 'AI Analysis'}</span>
                      </div>
                    </div>

                    <div className="knowledge-card-footer">
                      <span>Confidence</span>
                      <span className="knowledge-confidence-badge">{asset.confidence || 90}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
            {filteredWorkspaceAssets.length === 0 && (
              <div style={{ textAlign: 'center', padding: '48px', border: '1px dashed var(--border)', borderRadius: '8px', backgroundColor: 'var(--bg-card)', color: 'var(--text-muted)' }}>
                No documents imported in this workspace. Click "Import Document" to select from the global library.
              </div>
            )}
          </>
        )}
      </div>

      {/* Details drawer right panel */}
      {selectedAsset && (
        <div className="sliding-drawer">
          <div className="drawer-header">
            <h3>Details</h3>
            <button className="drawer-close" onClick={() => setSelectedAsset(null)}>
              <X size={18} />
            </button>
          </div>

          <div className="drawer-file-meta-header">
            <div className="knowledge-file-icon">
              <FileText size={22} />
            </div>
            <div className="drawer-file-meta-text">
              <h3>{selectedAsset.name}</h3>
              <p>{selectedAsset.size || '1.2 MB'} • PDF Document</p>
            </div>
          </div>

          <div className="drawer-tabs">
            <button
              className={`drawer-tab ${activeDrawerTab === 'details' ? 'active' : ''}`}
              onClick={() => setActiveDrawerTab('details')}
            >
              Details
            </button>
            <button
              className={`drawer-tab ${activeDrawerTab === 'preview' ? 'active' : ''}`}
              onClick={() => setActiveDrawerTab('preview')}
            >
              Preview
            </button>
            <button
              className={`drawer-tab ${activeDrawerTab === 'activity' ? 'active' : ''}`}
              onClick={() => setActiveDrawerTab('activity')}
            >
              Activity
            </button>
          </div>

          <div className="drawer-scroll-content">
            {activeDrawerTab === 'details' && (
              <div>
                <h4 className="drawer-section-title">Document Metadata</h4>
                <div className="drawer-metadata-list">
                  <div className="drawer-metadata-item">
                    <div className="drawer-metadata-item-icon">
                      <FileText size={16} />
                    </div>
                    <div className="drawer-metadata-item-text">
                      <h4>Knowledge Schema</h4>
                      <p>{selectedAsset.processing_metadata?.schema_selected || 'General Schema'}</p>
                    </div>
                  </div>

                  <div className="drawer-metadata-item">
                    <div className="drawer-metadata-item-icon">
                      <Layers size={16} />
                    </div>
                    <div className="drawer-metadata-item-text">
                      <h4>Chunking Strategy</h4>
                      <p>{selectedAsset.processing_metadata?.chunking_strategy || 'Default Chunker'}</p>
                      <div className="pill-row">
                        <span className="tag-pill">{selectedAsset.processing_metadata?.chunk_profile || 'Standard'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="drawer-metadata-item">
                    <div className="drawer-metadata-item-icon">
                      <Cpu size={16} />
                    </div>
                    <div className="drawer-metadata-item-text">
                      <h4>Selection Method</h4>
                      <p>{selectedAsset.processing_metadata?.selection_method || 'AI Parser'}</p>
                    </div>
                  </div>

                  <div className="drawer-metadata-item">
                    <div className="drawer-metadata-item-icon success">
                      <Check size={16} />
                    </div>
                    <div className="drawer-metadata-item-text">
                      <h4>Confidence</h4>
                      <p>High confidence in content relevance and quality.</p>
                      <div className="pill-row">
                        <span className="tag-pill" style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}>
                          {selectedAsset.confidence}% Verified
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="drawer-metadata-item">
                    <div className="drawer-metadata-item-icon">
                      <HelpCircle size={16} />
                    </div>
                    <div className="drawer-metadata-item-text">
                      <h4>Processing Reasoning</h4>
                      <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                        {selectedAsset.processing_metadata?.reasoning}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {activeDrawerTab === 'preview' && (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                <p style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>File Description:</p>
                <p style={{ marginBottom: '16px', lineHeight: '1.4' }}>{selectedAsset.user_description || 'No description provided.'}</p>
                <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '6px', backgroundColor: 'var(--bg-main)', fontFamily: 'monospace', fontSize: '11px' }}>
                  [PDF Content Preview Mocked]
                </div>
              </div>
            )}
            {activeDrawerTab === 'activity' && (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                <p>• Document uploaded on {selectedAsset.created_at ? new Date(selectedAsset.created_at).toLocaleDateString() : 'recent'}</p>
                <p style={{ marginTop: '8px' }}>• Chunked into vector points in Qdrant store</p>
                <p style={{ marginTop: '8px' }}>• Selected into active workspaces ({workspace?.name})</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Import Document Modal */}
      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-card" style={{ maxWidth: '600px' }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Import Document to Workspace</h3>
              <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setShowImportModal(false)}>✕</button>
            </div>
            <div className="modal-body" style={{ padding: '24px' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '16px' }}>
                Select documents from your organization's library to make them available for decisions in <strong>{workspace?.name}</strong>.
              </p>
              
              <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '6px', backgroundColor: 'var(--bg-main)' }}>
                {assets.filter(asset => !workspace?.selected_knowledge_asset_ids?.includes(asset.id)).length === 0 ? (
                  <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                    No new documents available to import. Upload them globally first!
                  </div>
                ) : (
                  assets
                    .filter(asset => !workspace?.selected_knowledge_asset_ids?.includes(asset.id))
                    .map(asset => {
                      const isSelected = selectedImportAssetIds.includes(asset.id);
                      return (
                        <div
                          key={asset.id}
                          onClick={() => {
                            if (isSelected) {
                              setSelectedImportAssetIds(prev => prev.filter(id => id !== asset.id));
                            } else {
                              setSelectedImportAssetIds(prev => [...prev, asset.id]);
                            }
                          }}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '12px 16px',
                            borderBottom: '1px solid var(--border)',
                            cursor: 'pointer',
                            backgroundColor: isSelected ? 'var(--primary-light)' : 'transparent',
                            transition: 'background-color 0.2s'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <FileText size={18} style={{ color: isSelected ? 'var(--primary)' : 'var(--text-muted)' }} />
                            <div>
                              <strong style={{ fontSize: '13px', display: 'block', color: 'var(--text-main)' }}>{asset.name}</strong>
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{asset.size || '1.2 MB'} • {asset.content_type?.toUpperCase() || 'PDF'}</span>
                            </div>
                          </div>
                          <div style={{
                            width: '18px',
                            height: '18px',
                            borderRadius: '4px',
                            border: '1.5px solid var(--border)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backgroundColor: isSelected ? 'var(--primary)' : 'transparent',
                            borderColor: isSelected ? 'var(--primary)' : 'var(--border)'
                          }}>
                            {isSelected && <Check size={12} strokeWidth={3} style={{ color: '#fff' }} />}
                          </div>
                        </div>
                      );
                    })
                )}
              </div>
            </div>
            <div className="modal-footer" style={{ borderTop: '1px solid var(--border)', padding: '16px 24px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button className="btn btn-secondary" onClick={() => setShowImportModal(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleImportAssets}
                disabled={selectedImportAssetIds.length === 0}
              >
                Import Selected ({selectedImportAssetIds.length})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
