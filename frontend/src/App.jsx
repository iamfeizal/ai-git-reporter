import { useState, useEffect, useCallback, useRef } from 'react';
import Stepper from './components/Stepper';
import SetupStep from './components/SetupStep';
import DataCheckStep from './components/DataCheckStep';
import HITLStep1 from './components/HITLStep1';
import HITLStep2 from './components/HITLStep2';
import ResultStep from './components/ResultStep';
import Settings from './components/Settings';
import * as api from './api';

const INITIAL_CONFIG = {
  instance_id: '',
  project_id: '',
  start_date: '2026-08-01',
  end_date: '2026-08-31',
  month_year: 'Agustus 2026',
  gdocs_mode: 'direct',
  gdocs_document_id: '',
};

export default function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [config, setConfig] = useState(INITIAL_CONFIG);
  const [showSettings, setShowSettings] = useState(false);

  // Workflow state
  const [threadId, setThreadId] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null); // 'starting' | 'running' | 'paused' | 'completed' | 'error'
  const [interruptData, setInterruptData] = useState(null);
  const [workflowState, setWorkflowState] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState(null);

  const pollingRef = useRef(null);

  // --- Polling for workflow status ---
  const pollStatus = useCallback(async (tid) => {
    try {
      const status = await api.getWorkflowStatus(tid);

      if (status.has_interrupt && status.is_paused) {
        // Pipeline paused at HITL checkpoint
        clearInterval(pollingRef.current);
        pollingRef.current = null;
        setPipelineStatus('paused');
        setInterruptData(status.interrupt_data);

        // Determine which HITL step we're at
        if (status.interrupt_data?.type === 'hitl_l1_review') {
          markComplete(2);
          setCurrentStep(3);
        } else if (status.interrupt_data?.type === 'hitl_l2_review') {
          markComplete(3);
          setCurrentStep(4);
        }
      } else if (!status.is_paused) {
        // Pipeline completed
        clearInterval(pollingRef.current);
        pollingRef.current = null;
        setPipelineStatus('completed');

        // Fetch final state
        try {
          const state = await api.getWorkflowState(tid);
          setWorkflowState(state.state);
        } catch { /* ignore */ }

        markComplete(5);
        setCurrentStep(6);
      }
      // else: still running, keep polling
    } catch (e) {
      console.error('Polling error:', e);
    }
  }, []);

  // Start polling
  const startPolling = useCallback((tid) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(() => pollStatus(tid), 3000);
    // Also poll immediately
    pollStatus(tid);
  }, [pollStatus]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const markComplete = (step) => {
    setCompletedSteps((prev) => prev.includes(step) ? prev : [...prev, step]);
  };

  // --- Step Handlers ---

  // Step 1 → Step 2
  const handleSetupNext = () => {
    markComplete(1);
    setCurrentStep(2);
  };

  // Step 2 → Start pipeline (move to waiting state)
  const handleDataCheckNext = async () => {
    markComplete(2);
    setCurrentStep(3);
    setPipelineStatus('starting');
    setStatusMessage('Memulai pipeline AI...');
    setError(null);

    try {
      const result = await api.startWorkflow({
        instance_id: parseInt(config.instance_id),
        project_id: config.project_id,
        start_date: config.start_date,
        end_date: config.end_date,
        month_year: config.month_year,
      });

      setThreadId(result.thread_id);
      setPipelineStatus('running');
      setStatusMessage(`Pipeline dimulai — ${result.total_commits} commit. Klasifikasi L1 berjalan...`);

      // Start polling for status
      startPolling(result.thread_id);
    } catch (e) {
      setPipelineStatus('error');
      setError(e.message);
      setStatusMessage('');
    }
  };

  // HITL-1 Approve
  const handleHITL1Approve = async (correctedCommits) => {
    setPipelineStatus('running');
    setStatusMessage('Melanjutkan pipeline — Klasifikasi L2 & Clustering...');
    setCurrentStep(3); // Stay on step 3 showing loading

    try {
      await api.resumeWorkflow(threadId, {
        corrected_commits: correctedCommits,
      });

      // Start polling again for the next HITL checkpoint or completion
      startPolling(threadId);
    } catch (e) {
      setPipelineStatus('error');
      setError(e.message);
    }
  };

  // HITL-2 Approve
  const handleHITL2Approve = async (correctedClusters) => {
    setPipelineStatus('running');
    setStatusMessage('Generating Executive Summary & Narasi...');
    setCurrentStep(5);
    markComplete(4);

    try {
      await api.resumeWorkflow(threadId, {
        corrected_clusters: correctedClusters,
      });

      // Poll for completion
      startPolling(threadId);
    } catch (e) {
      setPipelineStatus('error');
      setError(e.message);
    }
  };

  // Reset everything
  const handleReset = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    setCurrentStep(1);
    setCompletedSteps([]);
    setConfig(INITIAL_CONFIG);
    setThreadId(null);
    setPipelineStatus(null);
    setInterruptData(null);
    setWorkflowState(null);
    setStatusMessage('');
    setError(null);
  };

  // --- Render current step content ---
  const renderStepContent = () => {
    // Show loading/running state
    if (pipelineStatus === 'starting' || pipelineStatus === 'running') {
      return (
        <div className="card animate-fade-in">
          <div className="pipeline-progress">
            <div className="spinner spinner-lg" />
            <div className="pipeline-status-text">
              <strong>{statusMessage || 'Pipeline berjalan...'}</strong>
              <br />
              <span className="text-sm text-muted">Mohon tunggu, proses ini mungkin memerlukan beberapa menit.</span>
            </div>
          </div>
        </div>
      );
    }

    // Show error
    if (pipelineStatus === 'error') {
      return (
        <div className="card animate-fade-in">
          <div className="alert alert-error">{error || 'Terjadi kesalahan.'}</div>
          <div className="flex justify-between items-center mt-lg">
            <button className="btn btn-secondary" onClick={handleReset}>🔄 Mulai Ulang</button>
            <button className="btn btn-primary" onClick={handleDataCheckNext}>🔁 Coba Lagi</button>
          </div>
        </div>
      );
    }

    switch (currentStep) {
      case 1:
        return <SetupStep config={config} setConfig={setConfig} onNext={handleSetupNext} />;
      case 2:
        return <DataCheckStep config={config} onNext={handleDataCheckNext} onBack={() => setCurrentStep(1)} />;
      case 3:
        if (pipelineStatus === 'paused' && interruptData?.type === 'hitl_l1_review') {
          return <HITLStep1 interruptData={interruptData} onApprove={handleHITL1Approve} onBack={() => setCurrentStep(2)} />;
        }
        return null; // Loading handled above
      case 4:
        if (pipelineStatus === 'paused' && interruptData?.type === 'hitl_l2_review') {
          return <HITLStep2 interruptData={interruptData} onApprove={handleHITL2Approve} onBack={() => setCurrentStep(3)} />;
        }
        return null;
      case 5:
        return (
          <div className="card animate-fade-in">
            <div className="pipeline-progress">
              <div className="spinner spinner-lg" />
              <div className="pipeline-status-text">
                <strong>Menyusun Executive Summary & Narasi Bisnis...</strong>
              </div>
            </div>
          </div>
        );
      case 6:
        return <ResultStep state={workflowState} onReset={handleReset} />;
      default:
        return null;
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h1 style={{
          background: 'linear-gradient(135deg, var(--accent-light), #a78bfa, #f472b6)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontSize: '1.75rem',
          fontWeight: 800,
          letterSpacing: '-0.03em',
        }}>
          AI Report System
        </h1>
        <p className="text-sm text-muted" style={{ marginTop: '4px' }}>
          GitLab → AI Analysis → Google Docs — dengan Human-in-the-Loop Review
        </p>
        <button
          onClick={() => setShowSettings(!showSettings)}
          style={{ marginTop: '12px', padding: '6px 12px', borderRadius: '20px', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', cursor: 'pointer' }}
        >
          {showSettings ? 'Kembali ke Pipeline' : '⚙️ Settings (GitLab & LLM)'}
        </button>
      </header>

      {showSettings ? (
        <Settings onClose={() => setShowSettings(false)} />
      ) : (
        <>
          {/* Stepper */}
          <Stepper
            currentStep={currentStep}
            onStepClick={(s) => completedSteps.includes(s) && setCurrentStep(s)}
            completedSteps={completedSteps}
          />

          {/* Step Content */}
          {renderStepContent()}
        </>
      )}

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        marginTop: '48px',
        paddingBottom: '24px',
        color: 'var(--text-muted)',
        fontSize: '0.75rem',
      }}>
        AI Report System v2.0 • Powered by LangGraph + Gemini
      </footer>
    </div>
  );
}
