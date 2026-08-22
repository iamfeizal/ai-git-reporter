import { useState, useEffect } from 'react';
import * as api from '../api';

export default function Settings({ onClose }) {
  const [gitlabs, setGitlabs] = useState([]);
  const [llms, setLlms] = useState([]);
  const [activeTab, setActiveTab] = useState('gitlab');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form states
  const [gitlabForm, setGitlabForm] = useState({ name: '', gitlab_url: 'https://gitlab.com', token: '' });
  const [llmForm, setLlmForm] = useState({ provider: 'gemini', model_name: 'gemini-3.5-flash-lite', api_key: '', base_url: '' });

  const fetchData = async () => {
    try {
      const [gData, lData] = await Promise.all([api.fetchGitLabs(), api.fetchLLMs()]);
      setGitlabs(gData);
      setLlms(lData);
    } catch (e) {
      setError('Gagal memuat data: ' + e.message);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddGitLab = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await api.createGitLab(gitlabForm);
      setSuccess('GitLab Instance berhasil ditambahkan!');
      setGitlabForm({ name: '', gitlab_url: 'https://gitlab.com', token: '' });
      fetchData();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteGitLab = async (id) => {
    if (!window.confirm('Hapus instance ini?')) return;
    try {
      await api.deleteGitLab(id);
      fetchData();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="card animate-fade-in" style={{ position: 'relative' }}>
      <button 
        onClick={onClose} 
        style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}
      >
        ✕
      </button>
      <div className="card-header">
        <h2 className="card-title">⚙️ Settings</h2>
      </div>

      <div className="flex gap-md" style={{ marginBottom: '16px' }}>
        <button className={`btn ${activeTab === 'gitlab' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('gitlab')}>GitLab Instances</button>
        <button className={`btn ${activeTab === 'llm' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('llm')}>LLM Configs</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {activeTab === 'gitlab' && (
        <div className="flex flex-col gap-lg">
          <div className="table-container">
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '8px' }}>Name</th>
                  <th style={{ padding: '8px' }}>URL</th>
                  <th style={{ padding: '8px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {gitlabs.map((g) => (
                  <tr key={g.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '8px' }}>{g.name}</td>
                    <td style={{ padding: '8px' }}>{g.gitlab_url}</td>
                    <td style={{ padding: '8px' }}>
                      <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem' }} onClick={() => handleDeleteGitLab(g.id)}>Hapus</button>
                    </td>
                  </tr>
                ))}
                {gitlabs.length === 0 && (
                  <tr><td colSpan="3" style={{ padding: '8px', textAlign: 'center', color: 'var(--text-muted)' }}>Belum ada data.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <form onSubmit={handleAddGitLab} className="flex flex-col gap-md" style={{ marginTop: '16px', padding: '16px', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Tambah GitLab Instance</h3>
            <div className="form-group">
              <label className="form-label">Nama (ex: GitLab Kantor)</label>
              <input type="text" className="input" required value={gitlabForm.name} onChange={e => setGitlabForm({...gitlabForm, name: e.target.value})} />
            </div>
            <div className="form-group">
              <label className="form-label">GitLab URL</label>
              <input type="url" className="input" required value={gitlabForm.gitlab_url} onChange={e => setGitlabForm({...gitlabForm, gitlab_url: e.target.value})} />
            </div>
            <div className="form-group">
              <label className="form-label">Personal Access Token (PAT)</label>
              <input type="password" className="input" required value={gitlabForm.token} onChange={e => setGitlabForm({...gitlabForm, token: e.target.value})} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Menambahkan...' : 'Simpan GitLab Instance'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'llm' && (
        <div className="flex flex-col gap-lg">
          <p className="text-muted">Manajemen LLM Config dapat dilakukan melalui API Backend secara langsung untuk saat ini.</p>
        </div>
      )}
    </div>
  );
}
