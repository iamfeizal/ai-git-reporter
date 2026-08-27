import React from 'react';

/**
 * ResultStep — Shows the final generated report results.
 * Formats inline code (backticks) and bold terms nicely.
 */
export default function ResultStep({ state, onReset }) {
  const executiveSummary = state?.executive_summary || '';
  const finalNarratives = state?.final_narratives || state?.final_clusters || [];
  const serviceSubDomains = state?.service_sub_domains || [];

  const coreNarratives = finalNarratives.filter(
    (n) => (n.category_level_1 === 'SYSTEM_CORE' || n.category_level_1 === 'SYSTEM_APP')
  );
  const serviceNarratives = finalNarratives.filter(
    (n) => (n.category_level_1 === 'APP_SERVICE' || n.category_level_1 === 'SERVICE_APP')
  );

  const documentUrl = state?.document_url || '';

  // Render text with `code` monospace and **bold**
  const renderFormattedText = (text) => {
    if (!text) return null;
    const paragraphs = text.split('\n\n');

    return paragraphs.map((p, pIdx) => {
      // Split tokens for `code` and **bold**
      const tokens = p.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);

      return (
        <p key={pIdx} style={{ marginBottom: '12px', lineHeight: 1.75, color: 'var(--text-secondary)' }}>
          {tokens.map((token, tIdx) => {
            if (token.startsWith('`') && token.endsWith('`') && token.length > 1) {
              return (
                <code
                  key={tIdx}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                    color: '#f43f5e',
                    fontSize: '0.85em',
                  }}
                >
                  {token.slice(1, -1)}
                </code>
              );
            }
            if (token.startsWith('**') && token.endsWith('**') && token.length > 3) {
              return (
                <strong key={tIdx} style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                  {token.slice(2, -2)}
                </strong>
              );
            }
            return token;
          })}
        </p>
      );
    });
  };

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h2 className="card-title">📄 Hasil Laporan Aktivitas Super App</h2>
        <span className="badge badge-success">✅ Selesai ({finalNarratives.length} Sub-Cluster)</span>
      </div>

      {documentUrl && (
        <div
          className="alert alert-success"
          style={{
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <strong>Dokumen Google Docs Siap:</strong>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Seluruh heading hierarki, narasi monospace fungsi, dan penanda visual telah disinkronkan.
            </div>
          </div>
          <a
            href={documentUrl}
            target="_blank"
            rel="noreferrer"
            className="btn btn-primary"
            style={{ fontWeight: 600 }}
          >
            🔗 Buka Google Docs
          </a>
        </div>
      )}

      {/* Executive Summary */}
      {executiveSummary && (
        <div style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.05rem', color: 'var(--accent-light)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📊</span> Ringkasan Eksekutif (Executive Summary)
          </h3>
          <div
            style={{
              background: 'var(--bg-glass)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              fontSize: '0.925rem',
            }}
          >
            {renderFormattedText(executiveSummary)}
          </div>
        </div>
      )}

      {/* Section 1: Sistem Inti */}
      {coreNarratives.length > 0 && (
        <div style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.05rem', color: 'var(--system-app)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🖥️</span> 1. Perbaikan & Pengembangan Sistem Inti Aplikasi ({coreNarratives.length} Sub-Cluster)
          </h3>
          {coreNarratives.map((n, i) => (
            <NarrativeCard key={i} item={n} renderFormattedText={renderFormattedText} />
          ))}
        </div>
      )}

      {/* Section 2: Layanan Aplikasi */}
      {serviceNarratives.length > 0 && (
        <div style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.05rem', color: 'var(--service-app)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⚙️</span> 2. Pengembangan & Pemeliharaan Layanan Aplikasi ({serviceNarratives.length} Sub-Cluster)
          </h3>
          {serviceNarratives.map((n, i) => {
            const sd = serviceSubDomains.find((s) => s.sub_domain_id === n.sub_domain_id);
            return (
              <NarrativeCard
                key={i}
                item={n}
                subDomainName={sd?.sub_domain_name}
                renderFormattedText={renderFormattedText}
              />
            );
          })}
        </div>
      )}

      {finalNarratives.length === 0 && (
        <div className="alert alert-warning">Tidak ada narasi yang dihasilkan.</div>
      )}

      <div className="flex justify-between items-center mt-lg">
        <button className="btn btn-secondary" onClick={onReset}>
          🔄 Buat Laporan Baru
        </button>
      </div>
    </div>
  );
}

function NarrativeCard({ item, subDomainName, renderFormattedText }) {
  const L2_BADGE = {
    FEATURE_UI: 'badge-feature',
    BUG_FIX: 'badge-bugfix',
    REFACTOR_PERF: 'badge-refactor',
    INFRA_CHORE: 'badge-infra',
  };

  const title = item.sub_cluster_title || item.cluster_title;

  return (
    <div
      style={{
        background: 'var(--bg-glass)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '16px 18px',
        marginBottom: '14px',
      }}
    >
      <div className="flex items-center gap-sm" style={{ marginBottom: '10px', flexWrap: 'wrap' }}>
        {subDomainName && (
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--service-app)' }}>
            [{subDomainName}]
          </span>
        )}
        <strong style={{ fontSize: '0.95rem' }}>{title}</strong>
        {item.category_level_2 && (
          <span className={`badge ${L2_BADGE[item.category_level_2] || 'badge-info'}`}>
            {item.category_level_2}
          </span>
        )}
      </div>

      <div style={{ fontSize: '0.875rem' }}>
        {renderFormattedText(item.business_narrative)}
      </div>

      {item.requires_visual && item.visual_placeholder_note && (
        <div
          style={{
            marginTop: '12px',
            padding: '10px 14px',
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '6px',
            fontSize: '0.8125rem',
            color: 'var(--warning)',
            fontWeight: 500,
          }}
        >
          📸 <strong>[TAMBAHKAN GAMBAR/DOKUMENTASI]</strong> — {item.visual_placeholder_note}
        </div>
      )}

      {item.commit_ids && item.commit_ids.length > 0 && (
        <div className="flex gap-xs" style={{ marginTop: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Git Commits:</span>
          {item.commit_ids.map((id) => (
            <span key={id} className="commit-id" style={{ fontSize: '0.6875rem' }}>
              {id}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
