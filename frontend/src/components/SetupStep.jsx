import { useState, useEffect } from 'react';
import * as api from '../api';

export default function SetupStep({ config, setConfig, onNext }) {
  const [gitlabs, setGitlabs] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.fetchGitLabs().then(setGitlabs).catch(() => {});
  }, []);

  useEffect(() => {
    if (!config.instance_id) {
      setProjects([]);
      return;
    }
    setLoadingProjects(true);
    api.fetchProjects(config.instance_id)
      .then(setProjects)
      .catch((e) => setStatus({ type: 'error', msg: `Gagal memuat proyek: ${e.message}` }))
      .finally(() => setLoadingProjects(false));
  }, [config.instance_id]);

  const canProceed = config.instance_id && config.project_id;

  const handleNext = () => {
    if (!canProceed) {
      setStatus({ type: 'error', msg: 'Pilih GitLab Instance dan Project terlebih dahulu.' });
      return;
    }
    setStatus(null);
    onNext();
  };

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">⚙️ Setup — Pilih Sumber Data</h2>
      </div>

      <div className="flex flex-col gap-lg">
        <div className="form-group">
          <label className="form-label">GitLab Instance</label>
          <select
            className="select"
            value={config.instance_id}
            onChange={(e) => setConfig({ ...config, instance_id: e.target.value, project_id: '' })}
          >
            <option value="">— Pilih Instance —</option>
            {gitlabs.map((g) => (
              <option key={g.id} value={g.id}>{g.name} ({g.gitlab_url})</option>
            ))}
          </select>
          {gitlabs.length === 0 && (
            <p className="text-xs text-muted">
              Belum ada GitLab Instance. Tambahkan di halaman Settings.
            </p>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Project</label>
          <select
            className="select"
            value={config.project_id}
            onChange={(e) => setConfig({ ...config, project_id: e.target.value })}
            disabled={!config.instance_id || loadingProjects}
          >
            <option value="">
              {loadingProjects ? 'Memuat proyek...' : '— Pilih Project —'}
            </option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name_with_namespace || p.name}</option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Tanggal Mulai</label>
            <input
              type="date"
              className="input"
              value={config.start_date}
              onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Tanggal Akhir</label>
            <input
              type="date"
              className="input"
              value={config.end_date}
              onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Label Bulan (opsional)</label>
          <input
            type="text"
            className="input"
            placeholder="Contoh: Agustus 2026"
            value={config.month_year}
            onChange={(e) => setConfig({ ...config, month_year: e.target.value })}
          />
        </div>

        {status && (
          <div className={`alert alert-${status.type}`}>{status.msg}</div>
        )}

        <div className="flex justify-between items-center">
          <div />
          <button className="btn btn-primary" onClick={handleNext}>
            Lanjut ke Data Check →
          </button>
        </div>
      </div>
    </div>
  );
}
