import React, { useState, useRef } from 'react';
import './App.css';

const API_BASE = 'http://localhost:8000/api/v1';

async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/resume/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Resume upload failed');
  return res.json();
}

async function createJD(text: string) {
  const res = await fetch(`${API_BASE}/jd/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_text: text }),
  });
  if (!res.ok) throw new Error('JD creation failed');
  return res.json();
}

async function startAnalysis(resumeId: number, jdId: number) {
  const res = await fetch(`${API_BASE}/analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, jd_id: jdId }),
  });
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.detail || 'Analysis start failed');
  }
  return res.json();
}

async function getAnalysisResult(id: number) {
  const res = await fetch(`${API_BASE}/analysis/${id}`);
  if (!res.ok) throw new Error('Fetch result failed');
  return res.json();
}

const CircularProgress = ({ score }: { score: number }) => {
  const percentage = score * 100;
  const sqSize = 140;
  const strokeWidth = 8;
  const radius = (sqSize - strokeWidth) / 2;
  const viewBox = `0 0 ${sqSize} ${sqSize}`;
  const dashArray = radius * Math.PI * 2;
  const dashOffset = dashArray - (dashArray * percentage) / 100;
  
  let circleClass = "low";
  if (percentage >= 80) circleClass = "high";
  else if (percentage >= 50) circleClass = "med";

  return (
    <svg width={sqSize} height={sqSize} viewBox={viewBox} className="circular-chart">
      <circle
        className="circle-bg"
        cx={sqSize / 2}
        cy={sqSize / 2}
        r={radius}
      />
      <circle
        className={`circle ${circleClass}`}
        cx={sqSize / 2}
        cy={sqSize / 2}
        r={radius}
        strokeDasharray={dashArray}
        strokeDashoffset={dashOffset}
        transform={`rotate(-90 ${sqSize / 2} ${sqSize / 2})`}
      />
      <text x="50%" y="50%" className="percentage" dominantBaseline="central">
        {percentage.toFixed(0)}%
      </text>
    </svg>
  );
};

function App() {
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [jdId, setJdId] = useState<number | null>(null);
  const [analysisId, setAnalysisId] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  const [status, setStatus] = useState<string>('idle');
  const [loading, setLoading] = useState<{ resume: boolean; jd: boolean; analysis: boolean }>({ resume: false, jd: false, analysis: false });
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const processFile = async (file: File) => {
    try {
      setLoading(p => ({ ...p, resume: true }));
      setFileName(file.name);
      const data = await uploadResume(file);
      setResumeId(data.id);
    } catch (err) {
      alert('Upload failed');
      setFileName('');
    } finally {
      setLoading(p => ({ ...p, resume: false }));
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleUploadChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleJDSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = (e.currentTarget as any).jdText.value;
    if (!text.trim()) return;
    try {
      setLoading(p => ({ ...p, jd: true }));
      const data = await createJD(text);
      setJdId(data.id);
    } catch (err) {
      alert('JD failed');
    } finally {
      setLoading(p => ({ ...p, jd: false }));
    }
  };

  const runAnalysis = async () => {
    if (!resumeId || !jdId) return;
    try {
      setStatus('processing');
      setLoading(p => ({ ...p, analysis: true }));
      const data = await startAnalysis(resumeId, jdId);
      setAnalysisId(data.analysis_id);
      pollResult(data.analysis_id);
    } catch (err) {
      console.error(err);
      setStatus('failed');
      alert(`Analysis failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setLoading(p => ({ ...p, analysis: false }));
    }
  };

  const pollResult = async (id: number) => {
    const interval = setInterval(async () => {
      try {
        const data = await getAnalysisResult(id);
        if (data.analysis.status === 'completed') {
          clearInterval(interval);
          setResult(data);
          setStatus('completed');
          setLoading(p => ({ ...p, analysis: false }));
        } else if (data.analysis.status === 'failed') {
          clearInterval(interval);
          setStatus('failed');
          setLoading(p => ({ ...p, analysis: false }));
        }
      } catch (e) {
        // ignore poll errors
      }
    }, 1500);
  };

  return (
    <div className="dashboard-layout">
      <nav className="top-nav">
        <div className="brand">
          Candor AI <span className="brand-tag">v2.0</span>
        </div>
      </nav>

      <main className="main-content">
        <div className="grid-layout">
          {/* LEFT: Inputs */}
          <div className="glass-card">
            <h2>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              Analysis Inputs
            </h2>

            <div className="form-group">
              <label>1. Candidate Resume (PDF)</label>
              <div 
                className={`upload-area ${dragActive ? 'active' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  accept=".pdf" 
                  className="upload-input" 
                  ref={fileInputRef}
                  onChange={handleUploadChange} 
                  disabled={loading.resume} 
                />
                <div className="upload-content">
                  <div className="upload-icon">
                    {loading.resume ? (
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="spinner"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
                    ) : (
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
                    )}
                  </div>
                  <div className="upload-text">
                    {loading.resume ? 'Parsing document securely...' : 'Click or Drag PDF here'}
                  </div>
                  {!loading.resume && <div className="upload-subtext">Max size: 5MB</div>}
                </div>
              </div>
              {resumeId && (
                <div className="success-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                  {fileName} (ID: {resumeId})
                </div>
              )}
            </div>

            <form onSubmit={handleJDSubmit} className="form-group">
              <label>2. Job Description Mapping</label>
              <textarea 
                className="text-area"
                name="jdText" 
                placeholder="Paste the target job description requirements here..." 
                disabled={loading.jd}
              ></textarea>
              <div style={{display:'flex', justifyContent:'flex-end', marginTop:'1rem'}}>
                <button type="submit" className="btn" disabled={loading.jd}>
                  {loading.jd ? 'Extracting Logic...' : 'Process JD'}
                </button>
              </div>
              {jdId && (
                <div className="success-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Ontology Rules Mapped (ID: {jdId})
                </div>
              )}
            </form>

            <div className="action-row">
              <button
                className="btn btn-primary"
                onClick={runAnalysis}
                disabled={!resumeId || !jdId || status === 'processing'}
              >
                {status === 'processing' ? 'Running Deterministic Match...' : 'Start Chain Analysis'}
              </button>
            </div>
          </div>

          {/* RIGHT: Results */}
          <div className="glass-card">
            <h2>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              Analysis Intelligence
            </h2>

            {status === 'idle' && !result && (
              <div className="results-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
                <p>Provide inputs and run analysis to view intelligence map.</p>
              </div>
            )}

            {status === 'processing' && (
              <div className="pulse-loader">
                <div className="spinner"></div>
                <div className="pulse-text">Interrogating Master Ontology for ID: {analysisId}...</div>
              </div>
            )}

            {status === 'completed' && result && (
              <div className="report-dashboard">
                
                <div className="score-dashboard">
                  <CircularProgress score={result.analysis.score} />
                  <div className="score-details">
                    <div className="score-title">Deterministic Compatibility</div>
                    <div className="score-subtitle">Mathmatically calculated through hardcoded ontology rules and experience penalization, eliminating LLM hallucination risks.</div>
                  </div>
                </div>

                {result.explanation && (
                  <div className="ai-insight">
                    <div className="ai-insight-header">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v4"/><path d="M12 18v4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M16.24 16.24l2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="M4.93 19.07l2.83-2.83"/><path d="M16.24 7.76l2.83-2.83"/></svg>
                      AI Summary Intelligence
                    </div>
                    <div className="ai-insight-content">
                      <p>{result.explanation.summary}</p>
                      {result.explanation.gaps_explained?.length > 0 && (
                        <ul className="gap-list">
                          {result.explanation.gaps_explained.map((gap: string, i: number) => (
                            <li key={i}>{gap}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                )}

                <div className="data-grid">
                  <div className="data-card">
                    <h4>Matches</h4>
                    <div className="tags-container">
                      {result.analysis.details.skill_analysis.matched.length === 0 ? <span className="tag">None Match</span> :
                        result.analysis.details.skill_analysis.matched.map((s: string) => (
                          <span className="tag match" key={s}>{s}</span>
                        ))
                      }
                    </div>
                  </div>

                  <div className="data-card">
                    <h4>Missing Critical</h4>
                    <div className="tags-container">
                      {result.analysis.details.skill_analysis.missing_critical.length === 0 ? <span className="tag match">No Critical Gaps</span> :
                        result.analysis.details.skill_analysis.missing_critical.map((s: string) => (
                          <span className="tag miss" key={s}>{s}</span>
                        ))
                      }
                    </div>
                  </div>

                  <div className="data-card" style={{ gridColumn: '1 / -1' }}>
                    <h4>Experience Check Gate</h4>
                    <div className="exp-stats">
                      <div className="exp-row">
                        <span>Required via JD</span>
                        <span>{result.analysis.details.experience_analysis.required_years} years</span>
                      </div>
                      <div className="exp-row">
                        <span>Extracted from Resume</span>
                        <span>{result.analysis.details.experience_analysis.actual_years} years</span>
                      </div>
                      <div className={`exp-row gap-val ${result.analysis.details.experience_analysis.gap < 0 ? 'bad' : 'ok'}`}>
                        <span>Variance</span>
                        <span>{result.analysis.details.experience_analysis.gap > 0 ? '+' : ''}{result.analysis.details.experience_analysis.gap} years</span>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
