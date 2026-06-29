import React, { useState } from 'react';
import { Upload, FileText, X, Cpu, HelpCircle, HardDrive, CheckCircle2, Loader2, Play } from 'lucide-react';
import { api } from '../services/api';

// Static schemas for hackathon
const STATIC_SCHEMAS = [
  { id: '', name: 'Auto Detect (Recommended)' },
  { id: 'resume-schema', name: 'Resume' },
  { id: 'policy-schema', name: 'Policy' },
  { id: 'contract-schema', name: 'Contract' },
  { id: 'vendor-schema', name: 'Vendor Proposal' },
  { id: 'finance-schema', name: 'Financial Report' },
  { id: 'invoice-schema', name: 'Invoice' },
  { id: 'custom-schema', name: 'Custom' }
];

const CHUNK_STRATEGIES = [
  'SlidingWindowChunker',
  'HeadingChunker',
  'ParagraphChunker',
  'HierarchicalChunker',
  'SingleDocumentChunker'
];

const CHUNK_PROFILES = [
  'SMALL',
  'MEDIUM',
  'LARGE',
  'XLARGE'
];

export default function UploadWizard({ workspace, user, onClose, onSuccess }) {
  // Wizard state: input -> analyzing -> review -> processing -> success
  const [step, setStep] = useState('input');

  // Input state
  const [uploadFile, setUploadFile] = useState(null);
  const [description, setDescription] = useState('');
  const [selectedSchemaId, setSelectedSchemaId] = useState('');

  // Analysis state
  const [analysisResult, setAnalysisResult] = useState(null);

  // Review (Editable) state
  const [editedSchemaId, setEditedSchemaId] = useState('');
  const [editedChunkStrategy, setEditedChunkStrategy] = useState('');
  const [editedChunkProfile, setEditedChunkProfile] = useState('');
  const [editedLifecycle, setEditedLifecycle] = useState('');
  const [editedMetadata, setEditedMetadata] = useState('');

  // Processing state
  const [processingStage, setProcessingStage] = useState(0); 
  const [uploadResult, setUploadResult] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleAnalyzeDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setStep('analyzing');
    try {
      const orgId = user.organization_ids?.[0];
      const result = await api.analyzeKnowledge(workspace?.id || null, orgId, description, uploadFile, selectedSchemaId || null);
      
      setAnalysisResult(result);
      
      // Initialize editable state
      setEditedSchemaId(result.schema_selected || '');
      setEditedChunkStrategy(result.chunking_strategy || '');
      setEditedChunkProfile(result.chunk_profile || '');
      setEditedLifecycle(result.suggested_lifecycle?.join(', ') || '');
      setEditedMetadata(result.suggested_metadata?.join(', ') || '');
      
      setStep('review');
    } catch (error) {
      console.error(error);
      alert('Failed to analyze document.');
      setStep('input');
    }
  };

  const handleStartProcessing = async () => {
    setStep('processing');
    setProcessingStage(0);
    
    // Simulate processing stages visually (fake timing for UI feedback, real API call in background)
    // 0: Uploading, 1: Processing, 2: Chunking, 3: Embedding, 4: Indexing
    const stages = setInterval(() => {
      setProcessingStage(prev => {
        if (prev < 4) return prev + 1;
        clearInterval(stages);
        return prev;
      });
    }, 1500);

    try {
      const orgId = user.organization_ids?.[0];
      // Send the overrides to the backend
      const result = await api.uploadKnowledge(
        workspace?.id || null, 
        orgId, 
        description, 
        uploadFile, 
        editedChunkStrategy, 
        editedChunkProfile, 
        editedSchemaId
      );
      
      clearInterval(stages);
      setProcessingStage(4);
      setUploadResult(result);
      setStep('success');
    } catch (error) {
      clearInterval(stages);
      console.error(error);
      alert('Failed to process document.');
      setStep('review');
    }
  };

  const handleFinish = () => {
    if (onSuccess && uploadResult) {
      const newAsset = {
        id: uploadResult.asset_id,
        name: uploadFile.name,
        content_type: uploadFile.name.endsWith('.pdf') ? 'pdf' : 'text',
        user_description: description,
        status: 'ready',
        created_at: new Date().toISOString(),
        size: `${(uploadFile.size / (1024 * 1024)).toFixed(1)} MB`,
        confidence: analysisResult?.confidence || 1.0,
        processing_metadata: {
          chunking_strategy: uploadResult.chunking_strategy,
          chunk_profile: uploadResult.chunk_profile,
          reasoning: uploadResult.processing_reasoning,
          selection_method: analysisResult?.selection_method || 'manual',
          schema_selected: uploadResult.schema_selected
        }
      };
      onSuccess(newAsset);
    } else {
      onClose();
    }
  };

  const preventClose = step === 'analyzing' || step === 'processing';

  return (
    <div className="modal-overlay" onClick={() => { if (!preventClose) onClose(); }}>
      <div className="modal-card" style={{ maxWidth: '720px', display: 'flex', flexDirection: 'column' }} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HardDrive size={18} /> Intelligent Knowledge Upload Wizard
          </h3>
          {!preventClose && (
            <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={onClose}>✕</button>
          )}
        </div>

        <div className="modal-body" style={{ padding: '32px' }}>
          
          {step === 'input' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
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
                    <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => setUploadFile(null)}>
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
                  placeholder="These are resumes for hiring Senior AI Engineers."
                  maxLength={300}
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  style={{ minHeight: '80px' }}
                />
              </div>

              <div className="wizard-step-card">
                <div className="wizard-step-header">
                  <div className="wizard-step-number">3</div>
                  <h3>Choose Knowledge Type (Static for Hackathon)</h3>
                </div>
                <select 
                  className="wizard-textarea" 
                  style={{ height: 'auto', padding: '10px' }}
                  value={selectedSchemaId}
                  onChange={e => setSelectedSchemaId(e.target.value)}
                >
                  {STATIC_SCHEMAS.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <button
                className="btn btn-primary"
                style={{ padding: '14px', width: '100%', height: 'auto', fontSize: '16px', display: 'flex', justifyContent: 'center', gap: '8px' }}
                onClick={handleAnalyzeDocument}
                disabled={!uploadFile}
              >
                <Cpu size={20} /> Analyze Document
              </button>
            </div>
          )}

          {step === 'analyzing' && (
            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
              <Loader2 className="spinner" size={48} style={{ color: 'var(--primary)', margin: '0 auto 20px auto' }} />
              <h3>AI Analysis in Progress</h3>
              <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>
                Analyzing document layout, semantics, and metadata fields to determine the optimal ingestion strategy...
              </p>
            </div>
          )}

          {step === 'review' && analysisResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                <Cpu size={32} style={{ color: 'var(--primary)', margin: '0 auto 12px auto' }} />
                <h3>Review AI Suggestions</h3>
                <p style={{ color: 'var(--text-muted)' }}>You can edit these parameters before processing begins.</p>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(34, 197, 94, 0.1)', color: '#22c55e', padding: '4px 12px', borderRadius: '16px', fontSize: '13px', marginTop: '12px' }}>
                  <CheckCircle2 size={14} /> Confidence: {(analysisResult.confidence * 100).toFixed(0)}%
                </div>
              </div>

              <div className="wizard-step-card">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>Suggested Knowledge Type</label>
                    <select 
                      className="wizard-textarea" 
                      style={{ height: 'auto', padding: '8px' }}
                      value={editedSchemaId}
                      onChange={e => setEditedSchemaId(e.target.value)}
                    >
                      {STATIC_SCHEMAS.filter(s => s.id !== '').map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                      {/* Fallback if AI suggested an unknown schema ID */}
                      {!STATIC_SCHEMAS.find(s => s.id === editedSchemaId) && editedSchemaId && (
                        <option value={editedSchemaId}>AI Suggested Schema ({editedSchemaId})</option>
                      )}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>Suggested Chunk Strategy</label>
                    <select 
                      className="wizard-textarea" 
                      style={{ height: 'auto', padding: '8px' }}
                      value={editedChunkStrategy}
                      onChange={e => setEditedChunkStrategy(e.target.value)}
                    >
                      {CHUNK_STRATEGIES.map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div style={{ marginTop: '16px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>Suggested Chunk Profile</label>
                  <select 
                    className="wizard-textarea" 
                    style={{ height: 'auto', padding: '8px' }}
                    value={editedChunkProfile}
                    onChange={e => setEditedChunkProfile(e.target.value)}
                  >
                    {CHUNK_PROFILES.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div style={{ marginTop: '16px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>Suggested Lifecycle (Comma separated)</label>
                  <textarea
                    className="wizard-textarea"
                    value={editedLifecycle}
                    onChange={e => setEditedLifecycle(e.target.value)}
                    style={{ minHeight: '60px' }}
                  />
                </div>

                <div style={{ marginTop: '16px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>Suggested Metadata Fields (Comma separated)</label>
                  <textarea
                    className="wizard-textarea"
                    value={editedMetadata}
                    onChange={e => setEditedMetadata(e.target.value)}
                    style={{ minHeight: '60px' }}
                  />
                </div>

                <div className="wizard-reasoning-box" style={{ marginTop: '16px' }}>
                  <HelpCircle size={16} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                  <div>
                    <strong style={{ fontSize: '11px', display: 'block', marginBottom: '2px' }}>AI Reasoning</strong>
                    <p>{analysisResult.processing_reasoning}</p>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button className="btn btn-secondary" onClick={() => setStep('input')}>Back</button>
                <button className="btn btn-primary" onClick={handleStartProcessing} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Play size={16} /> Start Processing
                </button>
              </div>
            </div>
          )}

          {step === 'processing' && (
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              <h3 style={{ marginBottom: '32px' }}>Ingesting Document</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '300px', margin: '0 auto', textAlign: 'left' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {processingStage > 0 ? <CheckCircle2 size={20} color="#22c55e" /> : (processingStage === 0 ? <Loader2 size={20} className="spinner" color="var(--primary)" /> : <div style={{width: 20}} />)}
                  <span style={{ color: processingStage >= 0 ? 'var(--text-primary)' : 'var(--text-muted)' }}>1. Uploading</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {processingStage > 1 ? <CheckCircle2 size={20} color="#22c55e" /> : (processingStage === 1 ? <Loader2 size={20} className="spinner" color="var(--primary)" /> : <div style={{width: 20}} />)}
                  <span style={{ color: processingStage >= 1 ? 'var(--text-primary)' : 'var(--text-muted)' }}>2. Processing</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {processingStage > 2 ? <CheckCircle2 size={20} color="#22c55e" /> : (processingStage === 2 ? <Loader2 size={20} className="spinner" color="var(--primary)" /> : <div style={{width: 20}} />)}
                  <span style={{ color: processingStage >= 2 ? 'var(--text-primary)' : 'var(--text-muted)' }}>3. Chunking & Generation</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {processingStage > 3 ? <CheckCircle2 size={20} color="#22c55e" /> : (processingStage === 3 ? <Loader2 size={20} className="spinner" color="var(--primary)" /> : <div style={{width: 20}} />)}
                  <span style={{ color: processingStage >= 3 ? 'var(--text-primary)' : 'var(--text-muted)' }}>4. Embedding Generation</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {processingStage > 4 ? <CheckCircle2 size={20} color="#22c55e" /> : (processingStage === 4 ? <Loader2 size={20} className="spinner" color="var(--primary)" /> : <div style={{width: 20}} />)}
                  <span style={{ color: processingStage >= 4 ? 'var(--text-primary)' : 'var(--text-muted)' }}>5. Indexing in Qdrant</span>
                </div>
              </div>
            </div>
          )}

          {step === 'success' && uploadResult && (
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(34, 197, 94, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px auto' }}>
                <CheckCircle2 size={32} color="#22c55e" />
              </div>
              <h3 style={{ marginBottom: '8px' }}>Upload Completed</h3>
              <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>Your document has been added to the Organization Knowledge Library.</p>
              
              <div className="wizard-step-card" style={{ textAlign: 'left', marginBottom: '32px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '13px' }}>
                  <div>
                    <strong style={{ color: 'var(--text-muted)' }}>Knowledge Type:</strong>
                    <div style={{ marginTop: '4px' }}>{STATIC_SCHEMAS.find(s => s.id === uploadResult.schema_selected)?.name || uploadResult.schema_selected || 'Unknown'}</div>
                  </div>
                  <div>
                    <strong style={{ color: 'var(--text-muted)' }}>Chunks Generated:</strong>
                    <div style={{ marginTop: '4px' }}>{uploadResult.chunks_created}</div>
                  </div>
                  <div>
                    <strong style={{ color: 'var(--text-muted)' }}>Chunk Strategy:</strong>
                    <div style={{ marginTop: '4px' }}>{uploadResult.chunking_strategy}</div>
                  </div>
                  <div>
                    <strong style={{ color: 'var(--text-muted)' }}>Chunk Profile:</strong>
                    <div style={{ marginTop: '4px' }}>{uploadResult.chunk_profile}</div>
                  </div>
                  <div>
                    <strong style={{ color: 'var(--text-muted)' }}>Status:</strong>
                    <div style={{ marginTop: '4px', color: '#22c55e', fontWeight: 500 }}>Indexed Successfully</div>
                  </div>
                </div>
              </div>

              <button className="btn btn-primary" onClick={handleFinish} style={{ minWidth: '200px' }}>
                Done
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
