import React, { useState } from 'react';
import { Upload, FileText, X, Cpu, HelpCircle, HardDrive } from 'lucide-react';
import { api } from '../services/api';

export default function UploadWizard({ workspace, user, onClose, onSuccess }) {
  const [uploadFile, setUploadFile] = useState(null);
  const [description, setDescription] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleAnalyzeDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setAnalyzing(true);
    const orgId = user.organization_ids?.[0];
    const result = await api.uploadKnowledge(workspace?.id || null, orgId, description, uploadFile);
    setAnalysisResult(result);
    setAnalyzing(false);
  };

  const handleAddToKnowledge = () => {
    if (!analysisResult) return;

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

    if (onSuccess) {
      onSuccess(newAsset);
    }
  };

  return (
    <div className="modal-overlay" onClick={() => { if (!analyzing) onClose(); }}>
      <div className="modal-card" style={{ maxWidth: '960px', display: 'flex', flexDirection: 'column' }} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HardDrive size={18} /> Upload Document
          </h3>
          <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={onClose}>✕</button>
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
  );
}
