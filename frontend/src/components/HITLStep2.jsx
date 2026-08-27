import { useState } from 'react';

const L2_META = {
  FEATURE_UI: { label: 'Fitur & UI', badge: 'badge-feature', icon: '✨' },
  BUG_FIX: { label: 'Bug Fix', badge: 'badge-bugfix', icon: '🐛' },
  REFACTOR_PERF: { label: 'Refactor & Performa', badge: 'badge-refactor', icon: '⚡' },
  INFRA_CHORE: { label: 'Infra & Maintenance', badge: 'badge-infra', icon: '🔧' },
};

/**
 * HITL Checkpoint 2 — 4-Level Granular Tree Explorer & Full CRUD on Commits & Sub-Clusters.
 */
export default function HITLStep2({ interruptData, onApprove, onBack }) {
  const initialCore = interruptData?.core_system_clusters || [];
  const initialService = interruptData?.service_app_clusters || [];
  const initialSubDomains = interruptData?.service_sub_domains || [];
  const rawCommits = interruptData?.raw_commits || {};

  const [coreClusters, setCoreClusters] = useState(initialCore);
  const [serviceClusters, setServiceClusters] = useState(initialService);
  const [subDomains] = useState(initialSubDomains);

  // Active view tab: 'CORE' or sub_domain_id
  const [activeTab, setActiveTab] = useState('CORE');

  // Edit states
  const [editingItem, setEditingItem] = useState(null); // { type: 'CLUSTER' | 'SUB_CLUSTER' | 'COMMIT', id, text }
  const [showAddSubCluster, setShowAddSubCluster] = useState(null); // cluster_id
  const [newSubClusterTitle, setNewSubClusterTitle] = useState('');
  const [showAddManualTask, setShowAddManualTask] = useState(null); // sub_cluster_id
  const [manualTaskTitle, setManualTaskTitle] = useState('');

  // Expanded tree items
  const [expandedNodes, setExpandedNodes] = useState(new Set(['ALL']));

  const toggleExpand = (nodeId) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      next.has(nodeId) ? next.delete(nodeId) : next.add(nodeId);
      return next;
    });
  };

  const isExpanded = (nodeId) => expandedNodes.has('ALL') || expandedNodes.has(nodeId);

  // Helper to get active clusters
  const getActiveClusters = () => {
    if (activeTab === 'CORE') {
      return coreClusters;
    }
    return serviceClusters.filter((c) => (c.sub_domain_id || 'general') === activeTab);
  };

  // Helper to update active clusters
  const updateActiveClusters = (updater) => {
    if (activeTab === 'CORE') {
      setCoreClusters(updater);
    } else {
      setServiceClusters((prev) => {
        const others = prev.filter((c) => (c.sub_domain_id || 'general') !== activeTab);
        const current = prev.filter((c) => (c.sub_domain_id || 'general') === activeTab);
        const updated = typeof updater === 'function' ? updater(current) : updater;
        return [...others, ...updated];
      });
    }
  };

  // --- Cluster CRUD ---
  const handleRenameCluster = (clusterId, newTitle) => {
    if (!newTitle.trim()) return;
    updateActiveClusters((prev) =>
      prev.map((c) => (c.cluster_id === clusterId ? { ...c, cluster_title: newTitle.trim() } : c))
    );
    setEditingItem(null);
  };

  const handleDeleteCluster = (clusterId) => {
    if (!confirm('Hapus cluster ini beserta seluruh sub-cluster di dalamnya?')) return;
    updateActiveClusters((prev) => prev.filter((c) => c.cluster_id !== clusterId));
  };

  // --- Sub-Cluster CRUD ---
  const handleAddSubCluster = (clusterId) => {
    if (!newSubClusterTitle.trim()) return;
    const newSc = {
      sub_cluster_id: `sub-${Date.now()}`,
      sub_cluster_title: newSubClusterTitle.trim(),
      functional_scope: '',
      commit_ids: [],
    };
    updateActiveClusters((prev) =>
      prev.map((c) =>
        c.cluster_id === clusterId ? { ...c, sub_clusters: [...c.sub_clusters, newSc] } : c
      )
    );
    setNewSubClusterTitle('');
    setShowAddSubCluster(null);
  };

  const handleRenameSubCluster = (clusterId, subClusterId, newTitle) => {
    if (!newTitle.trim()) return;
    updateActiveClusters((prev) =>
      prev.map((c) =>
        c.cluster_id === clusterId
          ? {
              ...c,
              sub_clusters: c.sub_clusters.map((sc) =>
                sc.sub_cluster_id === subClusterId
                  ? { ...sc, sub_cluster_title: newTitle.trim() }
                  : sc
              ),
            }
          : c
      )
    );
    setEditingItem(null);
  };

  const handleDeleteSubCluster = (clusterId, subClusterId) => {
    if (!confirm('Hapus sub-cluster ini?')) return;
    updateActiveClusters((prev) =>
      prev.map((c) =>
        c.cluster_id === clusterId
          ? {
              ...c,
              sub_clusters: c.sub_clusters.filter((sc) => sc.sub_cluster_id !== subClusterId),
            }
          : c
      )
    );
  };

  const handleSplitSubCluster = (clusterId, subClusterId) => {
    updateActiveClusters((prev) =>
      prev.map((c) => {
        if (c.cluster_id !== clusterId) return c;
        const targetSc = c.sub_clusters.find((sc) => sc.sub_cluster_id === subClusterId);
        if (!targetSc || targetSc.commit_ids.length <= 1) {
          alert('Sub-cluster minimal harus memiliki 2 commit untuk dipecah.');
          return c;
        }
        const mid = Math.ceil(targetSc.commit_ids.length / 2);
        const part1Commits = targetSc.commit_ids.slice(0, mid);
        const part2Commits = targetSc.commit_ids.slice(mid);

        const sc1 = { ...targetSc, sub_cluster_title: `${targetSc.sub_cluster_title} (Bagian 1)`, commit_ids: part1Commits };
        const sc2 = {
          sub_cluster_id: `sub-${Date.now()}`,
          sub_cluster_title: `${targetSc.sub_cluster_title} (Bagian 2)`,
          functional_scope: '',
          commit_ids: part2Commits,
        };

        return {
          ...c,
          sub_clusters: c.sub_clusters.flatMap((sc) => (sc.sub_cluster_id === subClusterId ? [sc1, sc2] : [sc])),
        };
      })
    );
  };

  // --- Commit CRUD ---
  const handleAddManualTask = (clusterId, subClusterId) => {
    if (!manualTaskTitle.trim()) return;
    const manualId = `manual-${Date.now().toString().slice(-4)}`;
    updateActiveClusters((prev) =>
      prev.map((c) =>
        c.cluster_id === clusterId
          ? {
              ...c,
              sub_clusters: c.sub_clusters.map((sc) =>
                sc.sub_cluster_id === subClusterId
                  ? { ...sc, commit_ids: [...sc.commit_ids, manualId] }
                  : sc
              ),
            }
          : c
      )
    );
    rawCommits[manualId] = { short_id: manualId, title: manualTaskTitle.trim() };
    setManualTaskTitle('');
    setShowAddManualTask(null);
  };

  const handleDeleteCommit = (clusterId, subClusterId, commitId) => {
    updateActiveClusters((prev) =>
      prev.map((c) =>
        c.cluster_id === clusterId
          ? {
              ...c,
              sub_clusters: c.sub_clusters.map((sc) =>
                sc.sub_cluster_id === subClusterId
                  ? { ...sc, commit_ids: sc.commit_ids.filter((id) => id !== commitId) }
                  : sc
              ),
            }
          : c
      )
    );
  };

  const handleMoveCommit = (sourceClusterId, sourceSubClusterId, commitId, targetSubClusterId) => {
    if (sourceSubClusterId === targetSubClusterId) return;

    updateActiveClusters((prev) =>
      prev.map((c) => {
        return {
          ...c,
          sub_clusters: c.sub_clusters.map((sc) => {
            if (sc.sub_cluster_id === sourceSubClusterId) {
              return { ...sc, commit_ids: sc.commit_ids.filter((id) => id !== commitId) };
            }
            if (sc.sub_cluster_id === targetSubClusterId) {
              return { ...sc, commit_ids: [...sc.commit_ids, commitId] };
            }
            return sc;
          }),
        };
      })
    );
  };

  const handleApprove = () => {
    onApprove(coreClusters, serviceClusters);
  };

  const activeClusters = getActiveClusters();
  const allSubClustersInTab = activeClusters.flatMap((c) => c.sub_clusters);

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">🌳 Review & CRUD Hierarki Sub-Cluster (4-Level Tree)</h2>
        <span className="badge badge-info">
          {coreClusters.length + serviceClusters.length} Cluster • {coreClusters.flatMap(c => c.sub_clusters).length + serviceClusters.flatMap(c => c.sub_clusters).length} Sub-Cluster
        </span>
      </div>

      <p className="text-sm text-muted" style={{ marginBottom: '16px' }}>
        AI membagi commit ke dalam <strong>Sub-Cluster Fungsional Spesifik</strong> agar narasi tidak terlalu lebar.
        Anda dapat <strong>mengedit judul</strong>, <strong>memecah/menggabung</strong> sub-cluster, atau <strong>menambah/memindahkan commit</strong>.
      </p>

      {/* Navigation Tabs (Sistem Inti & Sub-Domains) */}
      <div className="flex gap-sm items-center mb-md" style={{ flexWrap: 'wrap', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
        <button
          className={`btn btn-sm ${activeTab === 'CORE' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('CORE')}
        >
          🖥️ Sistem Inti ({coreClusters.length} Cluster)
        </button>

        {subDomains.map((sd) => {
          const sClusters = serviceClusters.filter((c) => (c.sub_domain_id || 'general') === sd.sub_domain_id);
          const isActive = activeTab === sd.sub_domain_id;
          return (
            <button
              key={sd.sub_domain_id}
              className={`btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab(sd.sub_domain_id)}
            >
              📂 {sd.sub_domain_name} ({sClusters.length})
            </button>
          );
        })}
      </div>

      {/* Tree Explorer for Active Tab */}
      <div className="tree-view">
        {activeClusters.length === 0 ? (
          <div className="alert alert-info">Belum ada cluster pada kategori ini.</div>
        ) : (
          activeClusters.map((cluster) => {
            const meta = L2_META[cluster.category_level_2] || { label: cluster.category_level_2, badge: 'badge-info', icon: '📄' };
            const isClusterExpanded = isExpanded(cluster.cluster_id);

            return (
              <div key={cluster.cluster_id} className="tree-category mb-sm" style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
                {/* Level 3: ContextCluster Header */}
                <div
                  className="tree-category-header flex items-center justify-between"
                  style={{ background: 'var(--bg-glass)', padding: '10px 14px' }}
                >
                  <div className="flex items-center gap-sm" style={{ flex: 1 }}>
                    <span onClick={() => toggleExpand(cluster.cluster_id)} style={{ cursor: 'pointer', userSelect: 'none' }}>
                      {isClusterExpanded ? '▾' : '▸'}
                    </span>
                    <span>{meta.icon}</span>
                    <span className={`badge ${meta.badge}`}>{meta.label}</span>

                    {editingItem?.id === cluster.cluster_id ? (
                      <div className="flex gap-xs items-center" style={{ flex: 1 }}>
                        <input
                          className="form-input text-sm"
                          value={editingItem.text}
                          onChange={(e) => setEditingItem({ ...editingItem, text: e.target.value })}
                          style={{ padding: '2px 8px', height: '28px' }}
                          autoFocus
                        />
                        <button className="btn btn-sm btn-primary" onClick={() => handleRenameCluster(cluster.cluster_id, editingItem.text)}>✓</button>
                        <button className="btn btn-sm btn-secondary" onClick={() => setEditingItem(null)}>✕</button>
                      </div>
                    ) : (
                      <strong style={{ fontSize: '0.95rem' }}>{cluster.cluster_title}</strong>
                    )}
                  </div>

                  <div className="flex items-center gap-xs">
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => setEditingItem({ type: 'CLUSTER', id: cluster.cluster_id, text: cluster.cluster_title })}
                      title="Edit Judul Cluster"
                      style={{ padding: '2px 6px' }}
                    >
                      ✏️
                    </button>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => setShowAddSubCluster(cluster.cluster_id)}
                      title="Tambah Sub-Cluster Fungsional"
                      style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                    >
                      + Sub-Cluster
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDeleteCluster(cluster.cluster_id)}
                      title="Hapus Cluster"
                      style={{ padding: '2px 6px' }}
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                {/* Inline Add Sub-Cluster */}
                {showAddSubCluster === cluster.cluster_id && (
                  <div style={{ padding: '8px 16px', background: 'rgba(59, 130, 246, 0.05)', borderBottom: '1px dashed var(--border)' }}>
                    <div className="flex gap-xs items-center">
                      <input
                        className="form-input text-sm"
                        placeholder="Judul Sub-Cluster Fungsional (misal: Integrasi Notifikasi Push)..."
                        value={newSubClusterTitle}
                        onChange={(e) => setNewSubClusterTitle(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddSubCluster(cluster.cluster_id)}
                        autoFocus
                      />
                      <button className="btn btn-sm btn-primary" onClick={() => handleAddSubCluster(cluster.cluster_id)}>+ Simpan</button>
                      <button className="btn btn-sm btn-secondary" onClick={() => setShowAddSubCluster(null)}>Batal</button>
                    </div>
                  </div>
                )}

                {/* Level 4: Sub-Clusters */}
                {isClusterExpanded && (
                  <div style={{ padding: '8px 12px' }}>
                    {cluster.sub_clusters.map((subCluster) => (
                      <div
                        key={subCluster.sub_cluster_id}
                        style={{
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '6px',
                          padding: '10px 12px',
                          marginBottom: '8px',
                        }}
                      >
                        {/* Sub-Cluster Header */}
                        <div className="flex items-center justify-between mb-xs">
                          <div className="flex items-center gap-xs" style={{ flex: 1 }}>
                            <span style={{ color: 'var(--accent-light)', fontWeight: 700 }}>🔹</span>
                            {editingItem?.id === subCluster.sub_cluster_id ? (
                              <div className="flex gap-xs items-center" style={{ flex: 1 }}>
                                <input
                                  className="form-input text-sm"
                                  value={editingItem.text}
                                  onChange={(e) => setEditingItem({ ...editingItem, text: e.target.value })}
                                  style={{ padding: '2px 8px', height: '26px' }}
                                  autoFocus
                                />
                                <button className="btn btn-sm btn-primary" onClick={() => handleRenameSubCluster(cluster.cluster_id, subCluster.sub_cluster_id, editingItem.text)}>✓</button>
                                <button className="btn btn-sm btn-secondary" onClick={() => setEditingItem(null)}>✕</button>
                              </div>
                            ) : (
                              <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{subCluster.sub_cluster_title}</span>
                            )}
                            <span className="badge badge-info" style={{ fontSize: '0.6875rem' }}>
                              {subCluster.commit_ids.length} commit
                            </span>
                          </div>

                          <div className="flex items-center gap-xs">
                            <button
                              className="btn btn-sm btn-secondary"
                              style={{ padding: '2px 6px', fontSize: '0.7rem' }}
                              onClick={() => setEditingItem({ type: 'SUB_CLUSTER', id: subCluster.sub_cluster_id, text: subCluster.sub_cluster_title })}
                              title="Ubah Judul Sub-Cluster"
                            >
                              ✏️ Edit
                            </button>
                            {subCluster.commit_ids.length > 1 && (
                              <button
                                className="btn btn-sm btn-secondary"
                                style={{ padding: '2px 6px', fontSize: '0.7rem' }}
                                onClick={() => handleSplitSubCluster(cluster.cluster_id, subCluster.sub_cluster_id)}
                                title="Pecah menjadi 2 sub-cluster"
                              >
                                ✂️ Pecah
                              </button>
                            )}
                            <button
                              className="btn btn-sm btn-secondary"
                              style={{ padding: '2px 6px', fontSize: '0.7rem' }}
                              onClick={() => setShowAddManualTask(subCluster.sub_cluster_id)}
                              title="Tambah Task/Pekerjaan Manual"
                            >
                              + Task
                            </button>
                            <button
                              className="btn btn-sm btn-danger"
                              style={{ padding: '2px 6px', fontSize: '0.7rem' }}
                              onClick={() => handleDeleteSubCluster(cluster.cluster_id, subCluster.sub_cluster_id)}
                              title="Hapus Sub-Cluster"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>

                        {/* Inline Add Manual Task */}
                        {showAddManualTask === subCluster.sub_cluster_id && (
                          <div style={{ padding: '6px 8px', background: 'rgba(245, 158, 11, 0.08)', borderRadius: '4px', marginBottom: '8px' }}>
                            <div className="flex gap-xs items-center">
                              <input
                                className="form-input text-sm"
                                placeholder="Deskripsi pekerjaan/hotfix manual..."
                                value={manualTaskTitle}
                                onChange={(e) => setManualTaskTitle(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAddManualTask(cluster.cluster_id, subCluster.sub_cluster_id)}
                                autoFocus
                              />
                              <button className="btn btn-sm btn-primary" onClick={() => handleAddManualTask(cluster.cluster_id, subCluster.sub_cluster_id)}>+ Tambah</button>
                              <button className="btn btn-sm btn-secondary" onClick={() => setShowAddManualTask(null)}>Batal</button>
                            </div>
                          </div>
                        )}

                        {/* Commits in Sub-Cluster */}
                        <div style={{ paddingLeft: '12px', borderLeft: '2px solid var(--border-subtle)', marginTop: '6px' }}>
                          {subCluster.commit_ids.map((cid) => {
                            const commitObj = rawCommits[cid] || { short_id: cid, title: cid };
                            return (
                              <div
                                key={cid}
                                className="flex items-center justify-between"
                                style={{
                                  padding: '4px 8px',
                                  background: 'var(--bg-glass)',
                                  borderRadius: '4px',
                                  marginBottom: '4px',
                                  fontSize: '0.8125rem',
                                }}
                              >
                                <div className="flex items-center gap-xs" style={{ flex: 1 }}>
                                  <span className="commit-id" style={{ fontSize: '0.6875rem' }}>{cid}</span>
                                  <span style={{ color: 'var(--text-secondary)' }}>{commitObj.title}</span>
                                </div>

                                <div className="flex items-center gap-xs">
                                  {/* Move commit dropdown */}
                                  <select
                                    style={{
                                      fontSize: '0.7rem',
                                      padding: '1px 4px',
                                      background: 'var(--bg-primary)',
                                      color: 'var(--text-primary)',
                                      border: '1px solid var(--border-subtle)',
                                      borderRadius: '4px',
                                      maxWidth: '130px',
                                    }}
                                    value={subCluster.sub_cluster_id}
                                    onChange={(e) => handleMoveCommit(cluster.cluster_id, subCluster.sub_cluster_id, cid, e.target.value)}
                                  >
                                    <option disabled value={subCluster.sub_cluster_id}>Pindah ke...</option>
                                    {allSubClustersInTab
                                      .filter((sc) => sc.sub_cluster_id !== subCluster.sub_cluster_id)
                                      .map((sc) => (
                                        <option key={sc.sub_cluster_id} value={sc.sub_cluster_id}>
                                          {sc.sub_cluster_title}
                                        </option>
                                      ))}
                                  </select>

                                  <button
                                    className="btn btn-sm btn-danger"
                                    style={{ padding: '1px 5px', fontSize: '0.65rem' }}
                                    onClick={() => handleDeleteCommit(cluster.cluster_id, subCluster.sub_cluster_id, cid)}
                                    title="Keluarkan commit dari laporan"
                                  >
                                    ✕
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div className="flex justify-between items-center mt-lg">
        <button className="btn btn-secondary" onClick={onBack}>← Kembali ke Klasifikasi</button>
        <button className="btn btn-success" onClick={handleApprove}>
          ✅ Setujui & Mulai Looping Generate Dokumen
        </button>
      </div>
    </div>
  );
}
