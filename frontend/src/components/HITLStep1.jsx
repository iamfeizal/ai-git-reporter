import { useState, useCallback } from 'react';

/**
 * HITL Checkpoint 1 — Dual-column review of L1 classification (SYSTEM_APP vs SERVICE_APP).
 * Supports click-to-move between columns.
 */
export default function HITLStep1({ interruptData, commits, onApprove, onBack }) {
  // Initialize from interrupt data or commits
  const initialSystem = (interruptData?.system_app_commits || []);
  const initialService = (interruptData?.service_app_commits || []);

  const [systemCommits, setSystemCommits] = useState(initialSystem);
  const [serviceCommits, setServiceCommits] = useState(initialService);
  const [dragItem, setDragItem] = useState(null);
  const [dragOverColumn, setDragOverColumn] = useState(null);

  const totalCommits = systemCommits.length + serviceCommits.length;

  // Move commit from one column to the other
  const moveToService = useCallback((commit) => {
    setSystemCommits((prev) => prev.filter((c) => c.id !== commit.id));
    setServiceCommits((prev) => [...prev, { ...commit, category: 'SERVICE_APP' }]);
  }, []);

  const moveToSystem = useCallback((commit) => {
    setServiceCommits((prev) => prev.filter((c) => c.id !== commit.id));
    setSystemCommits((prev) => [...prev, { ...commit, category: 'SYSTEM_APP' }]);
  }, []);

  // Drag & Drop handlers
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
      ...systemCommits.map((c) => ({ ...c, category: 'SYSTEM_APP' })),
      ...serviceCommits.map((c) => ({ ...c, category: 'SERVICE_APP' })),
    ];
    onApprove(allCommits);
  };

  const CommitCard = ({ commit, onMove, moveLabel }) => (
    <div
      className={`commit-card ${dragItem?.commit?.id === commit.id ? 'dragging' : ''}`}
      draggable
      onDragStart={() => handleDragStart(commit, commit.category === 'SYSTEM_APP' ? 'system' : 'service')}
    >
      <span className="commit-id">{commit.id}</span>
      <div style={{ flex: 1 }}>
        <div className="commit-title">{commit.reason || commit.id}</div>
      </div>
      <button className="btn btn-sm btn-secondary" onClick={() => onMove(commit)} title={moveLabel}>
        {commit.category === 'SYSTEM_APP' ? '→' : '←'}
      </button>
    </div>
  );

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">👁️ Review Klasifikasi Level 1</h2>
        <span className="badge badge-info">{totalCommits} commit</span>
      </div>

      <p className="text-sm text-muted" style={{ marginBottom: '16px' }}>
        AI telah mengklasifikasikan commit ke <strong>Sistem Aplikasi</strong> dan <strong>Layanan Aplikasi</strong>.
        Klik tombol panah atau <em>drag-and-drop</em> untuk memindahkan commit yang salah klasifikasi.
      </p>

      <div className="dual-column">
        {/* System App Column */}
        <div className="column">
          <div className="column-header system">
            <span>🖥️ Sistem Aplikasi (SYSTEM_APP)</span>
            <span className="badge badge-system">{systemCommits.length}</span>
          </div>
          <div
            className={`column-body ${dragOverColumn === 'system' ? 'drag-over' : ''}`}
            onDragOver={(e) => handleDragOver(e, 'system')}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, 'system')}
          >
            {systemCommits.length === 0 ? (
              <div className="column-empty">Tidak ada commit di kategori ini</div>
            ) : (
              systemCommits.map((c) => (
                <CommitCard key={c.id} commit={c} onMove={moveToService} moveLabel="Pindah ke Service App" />
              ))
            )}
          </div>
        </div>

        {/* Service App Column */}
        <div className="column">
          <div className="column-header service">
            <span>⚙️ Layanan Aplikasi (SERVICE_APP)</span>
            <span className="badge badge-service">{serviceCommits.length}</span>
          </div>
          <div
            className={`column-body ${dragOverColumn === 'service' ? 'drag-over' : ''}`}
            onDragOver={(e) => handleDragOver(e, 'service')}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, 'service')}
          >
            {serviceCommits.length === 0 ? (
              <div className="column-empty">Tidak ada commit di kategori ini</div>
            ) : (
              serviceCommits.map((c) => (
                <CommitCard key={c.id} commit={c} onMove={moveToSystem} moveLabel="Pindah ke System App" />
              ))
            )}
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center mt-lg">
        <button className="btn btn-secondary" onClick={onBack}>← Kembali</button>
        <button className="btn btn-success" onClick={handleApprove}>
          ✅ Approve & Continue
        </button>
      </div>
    </div>
  );
}
