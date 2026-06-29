import React, { useState, useEffect } from 'react';
import { FileText, Upload, Plus, Check, ChevronRight, X, Shield, Cpu, Layers, HelpCircle, HardDrive } from 'lucide-react';
import { api } from '../services/api';

export default function Knowledge({ workspace, user, triggerOpenUpload, onCloseUploadTrigger }) {
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [activeDrawerTab, setActiveDrawerTab] = useState('details');
  const [showUploadWizard, setShowUploadWizard] = useState(false);
  const [loading, setLoading] = useState(false);

  // Upload States
  const [uploadFile, setUploadFile] = useState(null);
  const [description, setDescription] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  // Filter States
  const [filterDoc, setFilterDoc] = useState('all');
  const [filterWorkspace, setFilterWorkspace] = useState('all');
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    loadKnowledgeAssets();
  }, [workspace?.id]);

  useEffect(() => {
    if (triggerOpenUpload) {
      setShowUploadWizard(true);
      if (onCloseUploadTrigger) onCloseUploadTrigger();
    }
  }, [triggerOpenUpload]);

  const loadKnowledgeAssets = async () => {
    setLoading(true);
    const fetchedAssets = await api.getKnowledgeAssets();
    setAssets(fetchedAssets);
    if (fetchedAssets.length > 0) {
      setSelectedAsset(fetchedAssets[0]); // default select first card
    }
    setLoading(false);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleAnalyzeDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setAnalyzing(true);
    // Call upload API which runs indexing and analysis
    const orgId = user.organization_ids?.[0];
    const result = await api.uploadKnowledge(workspace?.id || 'ws1-uuid-0001', orgId, description, uploadFile);
    setAnalysisResult(result);
    setAnalyzing(false);
  };

  const handleAddToKnowledge = () => {
    if (!analysisResult) return;
    
    // Construct new asset card
    const newAsset = {
      id: analysisResult.asset_id,
      name: uploadFile.name,
      content_type: uploadFile.name.endsWith('.pdf') ? 'pdf' : 'text',
      user_description: description,
      status: 'ready',
      created_at: new Date().toISOString(),
      size: `${(uploadFile.size / (1024 * 1024)).toFixed(1)} MB`,
      confidence: analysisResult.confidence,
      processing_metadata: {
        chunking_strategy: analysisResult.chunking_strategy,
        chunk_profile: analysisResult.chunk_profile,
        reasoning: analysisResult.processing_reasoning,
        selection_method: analysisResult.selection_method,
        schema_selected: analysisResult.schema_selected
      }
    };
    
    setAssets(prev => [newAsset, ...prev]);
    setSelectedAsset(newAsset);
    
    // Reset Upload Flow
    setUploadFile(null);
    setDescription('');
    setAnalysisResult(null);
    setShowUploadWizard(false);
  };

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
            <button className="btn btn-primary" onClick={() => setShowUploadWizard(true)}>
              <Upload size={16} />
              <span>Upload Document</span>
            </button>
            <button className="btn btn-secondary btn-sm">
              <Plus size={16} />
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
          <select className="filter-select" value={filterWorkspace} onChange={e => setFilterWorkspace(e.target.value)}>
            <option value="all">All Workspaces</option>
            <option value="current">Current Workspace</option>
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
          <div className="knowledge-grid">
            {assets.map((asset) => {
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
              <p>{selectedAsset.size} • PDF Document</p>
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
                <p>• Document uploaded by Alex Johnson on {selectedAsset.created_at ? new Date(selectedAsset.created_at).toLocaleDateString() : 'recent'}</p>
                <p style={{ marginTop: '8px' }}>• Chunked into vector points in Qdrant store</p>
                <p style={{ marginTop: '8px' }}>• Selected into active workspaces (Acme Corporation, IT & Security)</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Interactive upload wizard modal */}
      {showUploadWizard && (
        <div className="modal-overlay" onClick={() => { if (!analyzing) setShowUploadWizard(false); }}>
          <div className="modal-card" style={{ maxWidth: '960px', display: 'flex', flexDirection: 'column' }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <HardDrive size={18} /> Upload Document
              </h3>
              <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setShowUploadWizard(false)}>✕</button>
            </div>

            <div className="modal-body" style={{ padding: '32px' }}>
              <div className="wizard-container">
                {/* Left Panel forms */}
                <div className="wizard-left-panel">
                  <div className="wizard-step-card">
                    <div className="wizard-step-header">
                      <div className="wizard-step-number">1</div>
                      <h3>Upload Document</h3>
                    </div>

                    {!uploadFile ? (
                      <label className="drag-drop-zone">
                        <Upload size={32} style={{ color: 'var(--primary)' }} />
                        <p><strong>Drag & drop your file here</strong></p>
                        <p className="file-types">or <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Browse Files</span></p>
                        <p className="file-types" style={{ color: 'var(--text-muted)' }}>Supports PDF, DOCX, TXT • Max size: 50MB</p>
                        <input type="file" style={{ display: 'none' }} accept=".pdf,.docx,.txt" onChange={handleFileChange} />
                      </label>
                    ) : (
                      <div className="uploaded-file-row">
                        <div className="uploaded-file-left">
                          <FileText size={20} style={{ color: '#ef4444' }} />
                          <div>
                            <strong style={{ fontSize: '13px', wordBreak: 'break-all' }}>{uploadFile.name}</strong>
                            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{(uploadFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                          </div>
                        </div>
                        <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => { setUploadFile(null); setAnalysisResult(null); }}>
                          <X size={16} />
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="wizard-step-card">
                    <div className="wizard-step-header">
                      <div className="wizard-step-number">2</div>
                      <h3>Describe this document in 2-3 lines</h3>
                    </div>

                    <textarea
                      className="wizard-textarea"
                      placeholder="This document describes our company's security compliance requirements."
                      maxLength={300}
                      value={description}
                      onChange={e => setDescription(e.target.value)}
                    />
                    <div className="character-counter">{description.length}/300</div>
                  </div>

                  <button
                    className="btn btn-primary"
                    style={{ padding: '12px', width: '100%', height: '44px' }}
                    onClick={handleAnalyzeDocument}
                    disabled={!uploadFile || analyzing}
                  >
                    {analyzing ? 'Analyzing Document with AI...' : 'Analyze Document'}
                  </button>
                </div>

                {/* Right Panel AI result */}
                <div className="wizard-right-panel">
                  <div>
                    <div className="wizard-analysis-title">
                      <Cpu size={18} />
                      <h3>AI Analysis Result</h3>
                    </div>
                    <p className="wizard-analysis-subtitle">Our AI has analyzed your document and extracted key information.</p>

                    {analysisResult ? (
                      <div className="wizard-results-list">
                        <div className="wizard-result-item">
                          <span className="label">Knowledge Schema</span>
                          <span className="wizard-result-pill purple">{analysisResult.schema_selected}</span>
                        </div>
                        <div className="wizard-result-item">
                          <span className="label">Chunking Strategy</span>
                          <span className="wizard-result-pill green">{analysisResult.chunking_strategy}</span>
                        </div>
                        <div className="wizard-result-item">
                          <span className="label">Chunk Profile</span>
                          <span className="wizard-result-pill blue">{analysisResult.chunk_profile}</span>
                        </div>
                        <div className="wizard-result-item">
                          <span className="label">Selection Method</span>
                          <span className="wizard-result-pill purple">{analysisResult.selection_method}</span>
                        </div>
                        <div className="wizard-result-item">
                          <span className="label">Confidence</span>
                          <span className="wizard-result-pill green">✓ {analysisResult.confidence}%</span>
                        </div>
                        
                        <div className="wizard-reasoning-box">
                          <HelpCircle size={16} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                          <div>
                            <strong style={{ fontSize: '11px', display: 'block', marginBottom: '2px' }}>Reasoning</strong>
                            <p>{analysisResult.processing_reasoning}</p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)', border: '1px dashed var(--border)', borderRadius: '8px', backgroundColor: 'var(--bg-main)' }}>
                        <Cpu size={24} style={{ marginBottom: '8px', opacity: 0.5 }} />
                        <p style={{ fontSize: '12px' }}>Upload and analyze your document to view structured extraction parameters in real-time.</p>
                      </div>
                    )}
                  </div>

                  <div className="wizard-actions-row">
                    <button className="btn btn-secondary" onClick={() => alert('View chunks modal is currently in mock.')} disabled={!analysisResult}>
                      View Chunks
                    </button>
                    <button className="btn btn-primary" onClick={handleAddToKnowledge} disabled={!analysisResult}>
                      Add to Knowledge
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
