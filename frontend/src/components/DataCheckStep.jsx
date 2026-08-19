import { useState } from 'react';
import * as api from '../api';

export default function DataCheckStep({ config, onNext, onBack }) {
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);
  const [totalCommits, setTotalCommits] = useState(0);
  const [sampleCommits, setSampleCommits] = useState([]);
  const [status, setStatus] = useState(null);

  const handleCheck = async () => {
    if (!config.instance_id || !config.project_id || !config.start_date || !config.end_date) {
      setStatus({ type: 'error', msg: 'Lengkapi semua field di langkah sebelumnya.' });
      return;
    }
    if (config.start_date > config.end_date) {
      setStatus({ type: 'error', msg: 'Tanggal mulai harus sebelum tanggal akhir.' });
      return;
    }

    setLoading(true);
    setStatus({ type: 'info', msg: 'Mengecek commit di GitLab...' });

    try {
      const result = await api.testGitLabCommits({
        instance_id: config.instance_id,
        project_id: config.project_id,
        start_date: config.start_date,
        end_date: config.end_date,
      });
      setTotalCommits(result.total_commits || 0);
      setSampleCommits(result.sample_commits || []);
      setChecked(true);

      if (result.total_commits > 0) {
        setStatus({ type: 'success', msg: `✅ Ditemukan ${result.total_commits} commit siap dianalisis.` });
      } else {
        setStatus({ type: 'warning', msg: '⚠️ Tidak ada commit pada rentang tanggal tersebut.' });
      }
    } catch (e) {
      setStatus({ type: 'error', msg: `Gagal: ${e.message}` });
    } finally {
      setLoading(false);
    }
  };

  const canProceed = checked && totalCommits > 0;

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">🔍 Data Check — Preview Commit</h2>
        <span className="badge badge-info">{config.start_date} → {config.end_date}</span>
      </div>

      <div className="flex flex-col gap-lg">
        <div className="flex items-center gap-md">
          <button className="btn btn-primary" onClick={handleCheck} disabled={loading}>
            {loading ? <><span className="spinner" /> Mengecek...</> : '🔎 Cek & Preview Commit'}
          </button>
          {checked && (
            <span className="text-sm text-muted">
              {totalCommits} commit ditemukan
            </span>
          )}
        </div>

        {status && (
          <div className={`alert alert-${status.type}`}>{status.msg}</div>
        )}

        {sampleCommits.length > 0 && (
          <div>
            <h3 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Sample Commit (maks 5):
            </h3>
            <div className="flex flex-col gap-sm">
              {sampleCommits.map((c, i) => (
                <div key={i} className="commit-card">
                  <span className="commit-id">{c.short_id}</span>
                  <div>
                    <div className="commit-title">{c.title}</div>
                    <div className="commit-meta">
                      {c.author_name} • {c.committed_date?.slice(0, 10)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-between items-center mt-md">
          <button className="btn btn-secondary" onClick={onBack}>← Kembali</button>
          <button className="btn btn-primary" onClick={onNext} disabled={!canProceed}>
            Mulai Pipeline AI →
          </button>
        </div>
      </div>
    </div>
  );
}
