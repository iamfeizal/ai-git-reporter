import { useState } from 'react';

const L2_LABELS = {
  FEATURE_UI: { label: 'Fitur & UI', badge: 'badge-feature', icon: '✨' },
  BUG_FIX: { label: 'Bug Fix', badge: 'badge-bugfix', icon: '🐛' },
  REFACTOR_PERF: { label: 'Refactor & Performa', badge: 'badge-refactor', icon: '⚡' },
  INFRA_CHORE: { label: 'Infra & Maintenance', badge: 'badge-infra', icon: '🔧' },
};

/**
 * HITL Checkpoint 2 — Tree-view of L2 categories and semantic clusters.
 * Supports renaming clusters, merging, and viewing commit details.
 */
export default function HITLStep2({ interruptData, onApprove, onBack }) {
  const initialClusters = interruptData?.clusters || [];
  const [clusters, setClusters] = useState(initialClusters);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [expandedCategories, setExpandedCategories] = useState(new Set(['SYSTEM_APP', 'SERVICE_APP']));

  // Group clusters by L1 → L2
  const grouped = {};
  clusters.forEach((cluster, idx) => {
    const l1 = cluster.category_level_1;
    const l2 = cluster.category_level_2;
    if (!grouped[l1]) grouped[l1] = {};
    if (!grouped[l1][l2]) grouped[l1][l2] = [];
    grouped[l1][l2].push({ ...cluster, _idx: idx });
  });

  const toggleCategory = (key) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const startEditing = (idx, title) => {
    setEditingId(idx);
    setEditTitle(title);
  };

  const saveTitle = (idx) => {
    setClusters((prev) => prev.map((c, i) => i === idx ? { ...c, cluster_title: editTitle } : c));
    setEditingId(null);
  };

  const mergeClusters = (l1, l2) => {
    const toMerge = clusters.filter((c) => c.category_level_1 === l1 && c.category_level_2 === l2);
    if (toMerge.length < 2) return;

    const merged = {
      cluster_title: toMerge[0].cluster_title,
      commit_ids: toMerge.flatMap((c) => c.commit_ids),
      category_level_1: l1,
      category_level_2: l2,
    };

    const remaining = clusters.filter((c) => !(c.category_level_1 === l1 && c.category_level_2 === l2));
    setClusters([...remaining, merged]);
  };

  const removeCluster = (idx) => {
    setClusters((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleApprove = () => {
    onApprove(clusters);
  };

  const L1_LABELS = {
    SYSTEM_APP: { label: 'Sistem Aplikasi', icon: '🖥️', headerClass: 'system' },
    SERVICE_APP: { label: 'Layanan & Infrastruktur', icon: '⚙️', headerClass: 'service' },
  };

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">🌳 Review Cluster & Sub-Kategori</h2>
        <span className="badge badge-info">{clusters.length} cluster</span>
      </div>

      <p className="text-sm text-muted" style={{ marginBottom: '16px' }}>
        AI telah mengelompokkan commit yang saling berkaitan ke dalam cluster.
        Anda dapat <strong>mengganti nama</strong> cluster, <strong>menggabungkan</strong> cluster dalam sub-kategori yang sama,
        atau <strong>menghapus</strong> cluster yang tidak relevan.
      </p>

      <div className="tree-view">
        {Object.entries(grouped).map(([l1, l2Groups]) => {
          const l1Info = L1_LABELS[l1] || { label: l1, icon: '📁', headerClass: '' };
          const l1Key = `l1-${l1}`;
          const isExpanded = expandedCategories.has(l1);

          return (
            <div key={l1} className="tree-category">
              <div className="tree-category-header" onClick={() => toggleCategory(l1)}>
                <div className="flex items-center gap-sm">
                  <span>{isExpanded ? '▾' : '▸'}</span>
                  <span style={{ fontSize: '1.1rem' }}>{l1Info.icon}</span>
                  <strong>{l1Info.label}</strong>
                  <span className={`badge badge-${l1 === 'SYSTEM_APP' ? 'system' : 'service'}`}>
                    {Object.values(l2Groups).flat().length} cluster
                  </span>
                </div>
              </div>

              {isExpanded && Object.entries(l2Groups).map(([l2, l2Clusters]) => {
                const l2Info = L2_LABELS[l2] || { label: l2, badge: 'badge-info', icon: '📄' };
                return (
                  <div key={l2} style={{ borderTop: '1px solid var(--border-subtle)' }}>
                    <div className="flex items-center justify-between" style={{ padding: '8px 16px 8px 32px', background: 'var(--bg-glass)' }}>
                      <div className="flex items-center gap-sm">
                        <span>{l2Info.icon}</span>
                        <span className="text-sm" style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{l2Info.label}</span>
                        <span className={`badge ${l2Info.badge}`}>{l2Clusters.length}</span>
                      </div>
                      {l2Clusters.length > 1 && (
                        <button className="btn btn-sm btn-secondary" onClick={() => mergeClusters(l1, l2)}>
                          🔗 Merge All
                        </button>
                      )}
                    </div>

                    {l2Clusters.map((cluster) => (
                      <div key={cluster._idx} className="tree-cluster">
                        <div className="tree-cluster-header">
                          {editingId === cluster._idx ? (
                            <>
                              <input
                                className="tree-cluster-title-input"
                                value={editTitle}
                                onChange={(e) => setEditTitle(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && saveTitle(cluster._idx)}
                                autoFocus
                              />
                              <button className="btn btn-sm btn-primary" onClick={() => saveTitle(cluster._idx)}>✓</button>
                              <button className="btn btn-sm btn-secondary" onClick={() => setEditingId(null)}>✕</button>
                            </>
                          ) : (
                            <>
                              <span className="tree-cluster-title">{cluster.cluster_title}</span>
                              <button
                                className="btn btn-sm btn-secondary"
                                onClick={() => startEditing(cluster._idx, cluster.cluster_title)}
                                title="Rename cluster"
                              >
                                ✏️
                              </button>
                              <button
                                className="btn btn-sm btn-danger"
                                onClick={() => removeCluster(cluster._idx)}
                                title="Remove cluster"
                              >
                                🗑️
                              </button>
                            </>
                          )}
                        </div>

                        <div style={{ marginLeft: '8px' }}>
                          {cluster.commit_ids.map((cid) => (
                            <div key={cid} className="tree-commit">
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>└</span>
                              <span className="commit-id">{cid}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>

      {clusters.length === 0 && (
        <div className="alert alert-warning mt-md">Tidak ada cluster untuk direview.</div>
      )}

      <div className="flex justify-between items-center mt-lg">
        <button className="btn btn-secondary" onClick={onBack}>← Kembali</button>
        <button className="btn btn-success" onClick={handleApprove} disabled={clusters.length === 0}>
          ✅ Approve & Generate Content
        </button>
      </div>
    </div>
  );
}
