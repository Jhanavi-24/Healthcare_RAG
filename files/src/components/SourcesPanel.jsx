import React from 'react';

const EV = {
  systematic_review: 'Systematic Review',
  rct: 'RCT',
  clinical_trial: 'Clinical Trial',
  guideline: 'Guideline',
  fda_label: 'FDA Label',
  cohort_study: 'Cohort Study',
  abstract: 'Abstract',
  case_report: 'Case Report',
  unknown: 'Reference',
};

function SourceCard({ c }) {
  return (
    <div className="source-card">
      <div className="source-top">
        <div className="source-num">{c.num}</div>
        <div className="source-title">{c.title}</div>
      </div>
      <span className="source-tag">
        {EV[c.evidence_type] || 'Reference'}
      </span>
      <div className="source-meta">
        {c.source ? c.source.toUpperCase() : ''} · {c.year}
        {c.confidence ? ' · ' + Math.round(c.confidence * 100) + '% confidence' : ''}
      </div>
      <SourceLink url={c.url} />
    </div>
  );
}

function SourceLink({ url }) {
  if (!url) return null;
  return (
    <a className="source-link" href={url} target="_blank" rel="noopener noreferrer">
      View source ↗
    </a>
  );
}

function EmptySources() {
  return (
    <div className="empty-sources">
      <div className="empty-icon">
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none" style={{ margin: '0 auto' }}>
          <rect x="7" y="4" width="18" height="26" rx="3" stroke="currentColor" strokeWidth="1.5" />
          <path d="M12 11h10M12 16h10M12 21h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </div>
      Ask a question and cited sources will show up here, numbered to match the answer.
    </div>
  );
}

export default function SourcesPanel({ citations }) {
  return (
    <aside className="sources-panel">
      <style>{`
        .sources-panel {
          background: var(--sidebar-bg);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-left: 1px solid var(--border);
          padding: 1.5rem 1.25rem;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }
        .sources-header { margin-bottom: 1.25rem; }
        .sources-title {
          font-size: 11px;
          font-weight: 700;
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin-bottom: 3px;
        }
        .sources-sub { font-size: 12.5px; color: var(--text-secondary); }
        .source-card {
          background: var(--panel-alpha);
          backdrop-filter: blur(10px);
          border: 1px solid var(--border-soft);
          border-radius: var(--radius-md);
          padding: 14px 16px;
          margin-bottom: 12px;
          box-shadow: var(--shadow-card);
          transition: transform 0.15s, box-shadow 0.15s;
        }
        .source-card:hover {
          transform: translateY(-1px);
          box-shadow: var(--shadow-panel);
        }
        .source-top {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          margin-bottom: 8px;
        }
        .source-num {
          width: 22px;
          height: 22px;
          border-radius: 6px;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white;
          font-size: 11px;
          font-weight: 700;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          box-shadow: 0 1px 4px rgba(61,139,114,0.4);
        }
        .source-title {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-primary);
          line-height: 1.4;
        }
        .source-tag {
          display: inline-block;
          font-size: 10px;
          font-weight: 600;
          padding: 2px 8px;
          border-radius: 4px;
          background: var(--sage-light);
          color: var(--sage-dark);
          margin-left: 32px;
          margin-bottom: 6px;
        }
        .source-meta {
          font-size: 11px;
          color: var(--text-tertiary);
          margin-left: 32px;
        }
        .source-link {
          font-size: 11.5px;
          color: var(--sage);
          text-decoration: none;
          margin-left: 32px;
          display: inline-block;
          margin-top: 5px;
          transition: color 0.15s;
        }
        .source-link:hover {
          color: var(--sage-dark);
          text-decoration: underline;
        }
        .empty-sources {
          text-align: center;
          padding: 3rem 1rem;
          color: var(--text-tertiary);
          font-size: 13px;
          line-height: 1.7;
        }
        .empty-icon { margin: 0 auto 12px; color: var(--border); }
      `}</style>

      <div className="sources-header">
        <div className="sources-title">Sources</div>
        <div className="sources-sub">
          {citations.length > 0
            ? citations.length + ' reference' + (citations.length > 1 ? 's' : '') + ' for this response'
            : 'References will appear here'}
        </div>
      </div>

      {citations.length === 0
        ? <EmptySources />
        : citations.map((c) => <SourceCard key={c.num} c={c} />)
      }
    </aside>
  );
}