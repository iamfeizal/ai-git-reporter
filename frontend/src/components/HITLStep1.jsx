import { useState, useCallback } from 'react';

/**
 * HITL Checkpoint 1 — Review & Full CRUD for Super App Sub-Domains & L1 Classification.
 * Left: Sistem Inti Aplikasi (SYSTEM_CORE)
 * Right: Layanan Aplikasi (APP_SERVICE) with Sub-Domain tabs and full CRUD.
 */
export default function HITLStep1({ interruptData, onApprove, onBack }) {
  const initialSystem = interruptData?.system_core_commits || interruptData?.system_app_commits || [];
  const initialService = interruptData?.service_app_commits || [];
  const initialSubDomains = interruptData?.service_sub_domains || [];

  const [systemCommits, setSystemCommits] = useState(initialSystem);
  const [serviceCommits, setServiceCommits] = useState(initialService);
  const [subDomains, setSubDomains] = useState(
    initialSubDomains.length > 0
      ? initialSubDomains
      : [{ sub_domain_id: 'general', sub_domain_name: 'Layanan Umum / General', description: '', commit_ids: [] }]
  );

  const [activeSubDomainId, setActiveSubDomainId] = useState(
    initialSubDomains[0]?.sub_domain_id || 'general'
  );

  // Modal / Form state for Sub-Domain CRUD
  const [showAddSubDomain, setShowAddSubDomain] = useState(false);
  const [newSubDomainName, setNewSubDomainName] = useState('');
  const [editingSubDomainId, setEditingSubDomainId] = useState(null);
  const [editSubDomainName, setEditSubDomainName] = useState('');

  const [dragItem, setDragItem] = useState(null);
  const [dragOverColumn, setDragOverColumn] = useState(null);

  const totalCommits = systemCommits.length + serviceCommits.length;

  // Active sub-domain commits
  const activeSubDomainCommits = serviceCommits.filter(
    (c) => (c.sub_domain_id || 'general') === activeSubDomainId
  );

  // Move commit to Active Sub-Domain
  const moveToService = useCallback(
    (commit) => {
      setSystemCommits((prev) => prev.filter((c) => c.id !== commit.id));
      setServiceCommits((prev) => {
        const filtered = prev.filter((c) => c.id !== commit.id);
        const sd = subDomains.find((s) => s.sub_domain_id === activeSubDomainId);
        return [
          ...filtered,
          {
            ...commit,
            category: 'APP_SERVICE',
            sub_domain_id: activeSubDomainId,
            sub_domain_name: sd?.sub_domain_name || 'Layanan Aplikasi',
          },
        ];
      });
    },
    [activeSubDomainId, subDomains]
  );

  // Move commit to System Core
  const moveToSystem = useCallback((commit) => {
    setServiceCommits((prev) => prev.filter((c) => c.id !== commit.id));
    setSystemCommits((prev) => [
      ...prev.filter((c) => c.id !== commit.id),
      { ...commit, category: 'SYSTEM_CORE', sub_domain_id: null, sub_domain_name: null },
    ]);
  }, []);

  // Transfer commit to another specific sub-domain
  const changeCommitSubDomain = (commitId, targetSubDomainId) => {
    const sd = subDomains.find((s) => s.sub_domain_id === targetSubDomainId);
    setServiceCommits((prev) =>
      prev.map((c) =>
        c.id === commitId
          ? {
              ...c,
              sub_domain_id: targetSubDomainId,
              sub_domain_name: sd?.sub_domain_name || targetSubDomainId,
            }
          : c
      )
    );
  };

  // Sub-Domain CRUD handlers
  const handleAddSubDomain = () => {
    if (!newSubDomainName.trim()) return;
    const slug = newSubDomainName
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-');
    const newSd = {
      sub_domain_id: slug || `service-${Date.now()}`,
      sub_domain_name: newSubDomainName.trim(),
      description: '',
      commit_ids: [],
    };
    setSubDomains((prev) => [...prev, newSd]);
    setActiveSubDomainId(newSd.sub_domain_id);
    setNewSubDomainName('');
    setShowAddSubDomain(false);
  };

  const handleSaveSubDomainName = (subDomainId) => {
    if (!editSubDomainName.trim()) return;
    setSubDomains((prev) =>
      prev.map((sd) =>
        sd.sub_domain_id === subDomainId ? { ...sd, sub_domain_name: editSubDomainName.trim() } : sd
      )
    );
    setEditingSubDomainId(null);
  };

  const handleDeleteSubDomain = (subDomainId) => {
    if (subDomains.length <= 1) {
      alert('Minimal harus terdapat 1 sub-domain layanan.');
      return;
    }
    if (!confirm('Hapus sub-domain ini? Commit di dalamnya akan dialihkan ke sub-domain pertama.')) {
      return;
    }
    const remaining = subDomains.filter((s) => s.sub_domain_id !== subDomainId);
    const fallbackId = remaining[0].sub_domain_id;

    // Reassign commits
    setServiceCommits((prev) =>
      prev.map((c) =>
        c.sub_domain_id === subDomainId
          ? { ...c, sub_domain_id: fallbackId, sub_domain_name: remaining[0].sub_domain_name }
          : c
      )
    );

    setSubDomains(remaining);
    setActiveSubDomainId(fallbackId);
  };

  // Drag & Drop
  const handleDragStart = (commit, source) => {
    setDragItem({ commit, source });
  };

  const handleDragOver = (e, column) => {
    e.preventDefault();
    setDragOverColumn(column);
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleDrop = (e, targetColumn) => {
    e.preventDefault();
    setDragOverColumn(null);
    if (!dragItem) return;

    const { commit, source } = dragItem;
    if (source === targetColumn) return;

    if (targetColumn === 'system') {
      moveToSystem(commit);
    } else {
      moveToService(commit);
    }
    setDragItem(null);
  };

  const handleApprove = () => {
    const allCommits = [
      ...systemCommits.map((c) => ({ ...c, category: 'SYSTEM_CORE' })),
      ...serviceCommits.map((c) => ({ ...c, category: 'APP_SERVICE' })),
    ];
    onApprove(allCommits, subDomains);
  };

  const activeSubDomain = subDomains.find((s) => s.sub_domain_id === activeSubDomainId);

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">👁️ Review Klasifikasi & Sub-Domain Layanan Super App</h2>
        <span className="badge badge-info">{totalCommits} total commit</span>
      </div>

      <p className="text-sm text-muted" style={{ marginBottom: '16px' }}>
        AI mengelompokkan commit ke <strong>Sistem Inti Aplikasi</strong> dan <strong>Layanan Aplikasi</strong> (per sub-domain app/modul).
        Anda dapat <strong>menambah/mengubah sub-domain</strong>, serta memindahkan commit antar domain atau modul layanan.
      </p>

      <div className="dual-column" style={{ gridTemplateColumns: '1fr 1.2fr', gap: '20px' }}>
        {/* Kolom Kiri: Sistem Inti */}
        <div className="column">
          <div className="column-header system">
            <span>🖥️ Sistem Inti Aplikasi (Core Platform)</span>
            <span className="badge badge-system">{systemCommits.length}</span>
          </div>
          <div
            className={`column-body ${dragOverColumn === 'system' ? 'drag-over' : ''}`}
            onDragOver={(e) => handleDragOver(e, 'system')}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, 'system')}
            style={{ maxHeight: '520px', overflowY: 'auto' }}
          >
            {systemCommits.length === 0 ? (
              <div className="column-empty">Tidak ada commit di Sistem Inti</div>
            ) : (
              systemCommits.map((c) => (
                <div
                  key={c.id}
                  className="commit-card"
                  draggable
                  onDragStart={() => handleDragStart(c, 'system')}
                >
                  <span className="commit-id">{c.id}</span>
                  <div style={{ flex: 1 }}>
                    <div className="commit-title" style={{ fontWeight: 600 }}>{c.title || c.id}</div>
                    {c.reason && <div className="text-sm text-muted" style={{ fontSize: '0.75rem' }}>{c.reason}</div>}
                  </div>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => moveToService(c)}
                    title={`Pindah ke ${activeSubDomain?.sub_domain_name || 'Layanan'}`}
                  >
                    →
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Kolom Kanan: Layanan Aplikasi & Sub-Domain CRUD */}
        <div className="column">
          <div className="column-header service flex justify-between items-center">
            <div className="flex items-center gap-sm">
              <span>⚙️ Layanan Aplikasi ({serviceCommits.length})</span>
            </div>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setShowAddSubDomain(true)}
              style={{ fontSize: '0.75rem', padding: '4px 8px' }}
            >
              + Tambah Layanan
            </button>
          </div>

          {/* Sub-Domain Management Tabs */}
          <div style={{ padding: '8px 12px', background: 'var(--bg-glass)', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="flex gap-sm items-center" style={{ flexWrap: 'wrap' }}>
              {subDomains.map((sd) => {
                const count = serviceCommits.filter((c) => (c.sub_domain_id || 'general') === sd.sub_domain_id).length;
                const isActive = activeSubDomainId === sd.sub_domain_id;
                return (
                  <div
                    key={sd.sub_domain_id}
                    onClick={() => setActiveSubDomainId(sd.sub_domain_id)}
                    style={{
                      cursor: 'pointer',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: isActive ? 'var(--service-app)' : 'var(--bg-secondary)',
                      color: isActive ? '#fff' : 'var(--text-secondary)',
                      fontSize: '0.8125rem',
                      fontWeight: isActive ? 600 : 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <span>{sd.sub_domain_name}</span>
                    <span style={{
                      background: isActive ? 'rgba(255,255,255,0.2)' : 'var(--bg-glass)',
                      padding: '1px 5px',
                      borderRadius: '10px',
                      fontSize: '0.7rem',
                    }}>
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Active Sub-Domain Controls: Rename / Delete */}
            {activeSubDomain && (
              <div className="flex items-center justify-between mt-sm" style={{ paddingTop: '6px', borderTop: '1px dashed var(--border-subtle)' }}>
                {editingSubDomainId === activeSubDomain.sub_domain_id ? (
                  <div className="flex gap-xs items-center" style={{ flex: 1 }}>
                    <input
                      className="form-input text-sm"
                      value={editSubDomainName}
                      onChange={(e) => setEditSubDomainName(e.target.value)}
                      placeholder="Nama Sub-Domain..."
                      style={{ padding: '4px 8px', height: '28px' }}
                    />
                    <button className="btn btn-sm btn-primary" onClick={() => handleSaveSubDomainName(activeSubDomain.sub_domain_id)}>✓</button>
                    <button className="btn btn-sm btn-secondary" onClick={() => setEditingSubDomainId(null)}>✕</button>
                  </div>
                ) : (
                  <div className="flex items-center gap-xs">
                    <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      📂 {activeSubDomain.sub_domain_name}
                    </span>
                    <button
                      className="btn btn-sm btn-secondary"
                      style={{ padding: '2px 6px', fontSize: '0.7rem' }}
                      onClick={() => {
                        setEditingSubDomainId(activeSubDomain.sub_domain_id);
                        setEditSubDomainName(activeSubDomain.sub_domain_name);
                      }}
                      title="Ubah Nama Layanan"
                    >
                      ✏️ Edit
                    </button>
                  </div>
                )}

                {subDomains.length > 1 && (
                  <button
                    className="btn btn-sm btn-danger"
                    style={{ padding: '2px 6px', fontSize: '0.7rem' }}
                    onClick={() => handleDeleteSubDomain(activeSubDomain.sub_domain_id)}
                    title="Hapus Sub-Domain"
                  >
                    🗑️ Hapus
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Modal / Inline Add Sub-Domain */}
          {showAddSubDomain && (
            <div style={{ padding: '8px 12px', background: 'rgba(59, 130, 246, 0.08)', borderBottom: '1px solid var(--accent)' }}>
              <div className="flex gap-xs items-center">
                <input
                  className="form-input text-sm"
                  placeholder="Nama Sub-Domain (misal: Layanan Pembayaran, Layanan Presensi)..."
                  value={newSubDomainName}
                  onChange={(e) => setNewSubDomainName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddSubDomain()}
                  autoFocus
                  style={{ padding: '4px 8px', height: '30px' }}
                />
                <button className="btn btn-sm btn-primary" onClick={handleAddSubDomain}>+ Tambah</button>
                <button className="btn btn-sm btn-secondary" onClick={() => setShowAddSubDomain(false)}>Batal</button>
              </div>
            </div>
          )}

          {/* Commits list for active sub-domain */}
          <div
            className={`column-body ${dragOverColumn === 'service' ? 'drag-over' : ''}`}
            onDragOver={(e) => handleDragOver(e, 'service')}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, 'service')}
            style={{ maxHeight: '430px', overflowY: 'auto' }}
          >
            {activeSubDomainCommits.length === 0 ? (
              <div className="column-empty">Tidak ada commit di {activeSubDomain?.sub_domain_name || 'layanan ini'}</div>
            ) : (
              activeSubDomainCommits.map((c) => (
                <div
                  key={c.id}
                  className="commit-card"
                  draggable
                  onDragStart={() => handleDragStart(c, 'service')}
                >
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => moveToSystem(c)}
                    title="Pindah ke Sistem Inti"
                  >
                    ←
                  </button>
                  <span className="commit-id">{c.id}</span>
                  <div style={{ flex: 1 }}>
                    <div className="commit-title" style={{ fontWeight: 600 }}>{c.title || c.id}</div>
                    {/* Transfer to another sub-domain dropdown */}
                    <div className="flex items-center gap-xs mt-xs">
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Pindah modul:</span>
                      <select
                        value={c.sub_domain_id || 'general'}
                        onChange={(e) => changeCommitSubDomain(c.id, e.target.value)}
                        style={{
                          fontSize: '0.7rem',
                          padding: '2px 4px',
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '4px',
                        }}
                      >
                        {subDomains.map((s) => (
                          <option key={s.sub_domain_id} value={s.sub_domain_id}>
                            {s.sub_domain_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center mt-lg">
        <button className="btn btn-secondary" onClick={onBack}>← Kembali</button>
        <button className="btn btn-success" onClick={handleApprove}>
          ✅ Simpan & Lanjut ke Granular Clustering
        </button>
      </div>
    </div>
  );
}
