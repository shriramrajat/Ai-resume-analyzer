
import React, { useState } from 'react';
import './App.css';

// --- API CLIENT ---
const API_BASE = 'http://localhost:8000/api/v1';

async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  // Assuming /resume/upload based on Phase 2 defaults
  const res = await fetch(`${API_BASE}/resume/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Resume upload failed');
  return res.json();
}

async function createJD(text: string) {
  // Assuming /jd/create based on Phase 4 defaults
  const res = await fetch(`${API_BASE}/jd/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_text: text }),
  });
  if (!res.ok) throw new Error('JD creation failed');
  return res.json();
}

async function startAnalysis(resumeId: number, jdId: number) {
  // Confirmed /analysis in Phase 7
  const res = await fetch(`${API_BASE}/analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, jd_id: jdId }),
  });
  if (!res.ok) throw new Error('Analysis start failed');
  return res.json();
}

async function getAnalysisResult(id: number) {
  const res = await fetch(`${API_BASE}/analysis/${id}`);
  if (!res.ok) throw new Error('Fetch result failed');
  return res.json();
}

// --- COMPONENTS ---

function App() {
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [jdId, setJdId] = useState<number | null>(null);
  const [analysisId, setAnalysisId] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  const [status, setStatus] = useState<string>('idle');
  const [loading, setLoading] = useState(false);

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    try {
      setLoading(true);
      const data = await uploadResume(e.target.files[0]);
      setResumeId(data.id);
      alert('Resume Uploaded!');
    } catch (err) {
      alert('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleJDSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = (e.currentTarget as any).jdText.value;
    try {
      setLoading(true);
      const data = await createJD(text);
      setJdId(data.id);
      alert('JD Processed! Skills Extracted.');
    } catch (err) {
      alert('JD failed');
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    if (!resumeId || !jdId) return;
    try {
      setStatus('starting');
      const data = await startAnalysis(resumeId, jdId);
      setAnalysisId(data.analysis_id);
      pollResult(data.analysis_id);
    } catch (err) {
      alert('Analysis failed to start');
    }
  };

  const pollResult = async (id: number) => {
    setStatus('processing');
    const interval = setInterval(async () => {
      try {
        const data = await getAnalysisResult(id);
        if (data.analysis.status === 'completed') {
          clearInterval(interval);
          setResult(data);
          setStatus('completed');
        } else if (data.analysis.status === 'failed') {
          clearInterval(interval);
          setStatus('failed');
        }
      } catch (e) {
        // ignore poll errors
      }
    }, 1000);
  };

  return (
    <div className="container">
      <header>
        <h1>AI Resume Analyzer <span className="tag">Engine v1.0</span></h1>
      </header>

      <div className="grid">
        {/* INPUT SECTION */}
        <div className="card">
          <h2>1. Inputs</h2>

          <div className="input-group">
            <label>Upload Resume (PDF)</label>
            <input type="file" accept=".pdf" onChange={handleResumeUpload} disabled={loading} />
            {resumeId && <span className="success">✅ Resume ID: {resumeId}</span>}
          </div>

          <form onSubmit={handleJDSubmit} className="input-group">
            <label>Paste Job Description</label>
            <textarea name="jdText" rows={6} placeholder="Paste JD here..." disabled={loading}></textarea>
            <button type="submit" disabled={loading}>Process JD</button>
            {jdId && <span className="success">✅ JD ID: {jdId}</span>}
          </form>

          <div className="action-area">
            <button
              className="analyze-btn"
              onClick={runAnalysis}
              disabled={!resumeId || !jdId || status === 'processing'}
            >
              {status === 'processing' ? 'Analyzing...' : 'Run Analysis Chain'}
            </button>
          </div>
        </div>

        {/* RESULTS SECTION */}
        <div className="card results">
          <h2>2. Analysis Results</h2>

          {status === 'processing' && (
            <div className="loader">
              ⚠️ Engine is crunching data... (Analysis ID: {analysisId})
            </div>
          )}

          {result && (
            <div className="report">
              <div className="score-box">
                <span className="label">Match Score</span>
                <span className="score">{(result.analysis.score * 100).toFixed(0)}%</span>
              </div>

              <h3>🔍 AI Explanation</h3>
              <div className="ai-box">
                <p><strong>Summary:</strong> {result.explanation?.summary}</p>
                <p><strong>Gap Analysis:</strong></p>
                <ul>
                  {result.explanation?.gaps_explained?.map((g: string, i: number) => <li key={i}>{g}</li>)}
                </ul>
              </div>

              <h3>📊 Structured Data (The Truth)</h3>
              <div className="structured-box">
                <div className="section">
                  <h4>Matches</h4>
                  {result.analysis.details.skill_analysis.matched.map((s: string) => (
                    <span className="badge match" key={s}>{s}</span>
                  ))}
                </div>

                <div className="section">
                  <h4>Missing Critical (Red Flags)</h4>
                  {result.analysis.details.skill_analysis.missing_critical.length === 0 ? <span>None</span> :
                    result.analysis.details.skill_analysis.missing_critical.map((s: string) => (
                      <span className="badge miss" key={s}>{s}</span>
                    ))
                  }
                </div>

                <div className="section">
                  <h4>Experience Gap</h4>
                  <p>Required: {result.analysis.details.experience_analysis.required_years} years</p>
                  <p>Actual: {result.analysis.details.experience_analysis.actual_years} years</p>
                  <p className={result.analysis.details.experience_analysis.gap < 0 ? 'error' : 'success'}>
                    Gap: {result.analysis.details.experience_analysis.gap} years
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
