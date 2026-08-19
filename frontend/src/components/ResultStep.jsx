/**
 * ResultStep — Shows the final generated report results.
 * Displays executive summary and cluster narratives.
 */
export default function ResultStep({ state, onReset }) {
  const executiveSummary = state?.executive_summary || '';
  const finalClusters = state?.final_clusters || [];

  const systemClusters = finalClusters.filter((c) => c.category_level_1 === 'SYSTEM_APP');
  const serviceClusters = finalClusters.filter((c) => c.category_level_1 === 'SERVICE_APP');

  const documentUrl = state?.document_url || '';

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">📄 Hasil Laporan</h2>
        <span className="badge badge-success">✅ Selesai</span>
      </div>

      {documentUrl && (
        <div className="alert alert-success" style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Tautan Google Docs:</span>
          <a href={documentUrl} target="_blank" rel="noreferrer" className="btn btn-primary btn-sm">
            Buka Dokumen
          </a>
        </div>
      )}

      {executiveSummary && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--accent-light)', marginBottom: '12px' }}>
            Executive Summary
          </h3>
          <div style={{
            background: 'var(--bg-glass)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            lineHeight: 1.8,
            color: 'var(--text-secondary)',
            fontSize: '0.9rem',
            whiteSpace: 'pre-wrap',
          }}>
            {executiveSummary}
          </div>
        </div>
      )}

      {systemClusters.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--system-app)', marginBottom: '12px' }}>
            🖥️ Perbaikan & Pengembangan Sistem Aplikasi ({systemClusters.length} cluster)
          </h3>
          {systemClusters.map((cluster, i) => (
            <ClusterCard key={i} cluster={cluster} />
          ))}
        </div>
      )}

      {serviceClusters.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--service-app)', marginBottom: '12px' }}>
            ⚙️ Pemeliharaan Layanan & Infrastruktur ({serviceClusters.length} cluster)
          </h3>
          {serviceClusters.map((cluster, i) => (
            <ClusterCard key={i} cluster={cluster} />
          ))}
        </div>
      )}

      {finalClusters.length === 0 && (
        <div className="alert alert-warning">Tidak ada cluster yang dihasilkan.</div>
      )}

      <div className="flex justify-between items-center mt-lg">
        <button className="btn btn-secondary" onClick={onReset}>
          🔄 Buat Laporan Baru
        </button>
      </div>
    </div>
  );
}

function ClusterCard({ cluster }) {
  const L2_BADGE = {
    FEATURE_UI: 'badge-feature',
    BUG_FIX: 'badge-bugfix',
    REFACTOR_PERF: 'badge-refactor',
    INFRA_CHORE: 'badge-infra',
  };

  return (
    <div style={{
      background: 'var(--bg-glass)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: '16px',
      marginBottom: '12px',
    }}>
      <div className="flex items-center gap-sm" style={{ marginBottom: '8px' }}>
        <strong style={{ fontSize: '0.9rem' }}>{cluster.cluster_title}</strong>
        <span className={`badge ${L2_BADGE[cluster.category_level_2] || 'badge-info'}`}>
          {cluster.category_level_2}
        </span>
      </div>

      <p style={{
        color: 'var(--text-secondary)',
        fontSize: '0.875rem',
        lineHeight: 1.7,
        whiteSpace: 'pre-wrap',
      }}>
        {cluster.business_narrative}
      </p>

      {cluster.requires_visual && cluster.visual_placeholder_note && (
        <div style={{
          marginTop: '12px',
          padding: '8px 12px',
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.2)',
          borderRadius: '6px',
          fontSize: '0.8125rem',
          color: 'var(--warning)',
        }}>
          📸 {cluster.visual_placeholder_note}
        </div>
      )}

      <div className="flex gap-sm" style={{ marginTop: '8px', flexWrap: 'wrap' }}>
        {cluster.commit_ids?.map((id) => (
          <span key={id} className="commit-id" style={{ fontSize: '0.6875rem' }}>{id}</span>
        ))}
      </div>
    </div>
  );
}
