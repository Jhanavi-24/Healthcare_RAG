import React, { useState } from 'react';

const EV_META = {
  systematic_review: { label: 'Systematic Review', tier: 'green' },
  rct:               { label: 'RCT',               tier: 'green' },
  clinical_trial:    { label: 'Clinical Trial',    tier: 'blue'  },
  guideline:         { label: 'Guideline',          tier: 'blue'  },
  fda_label:         { label: 'FDA Label',          tier: 'amber' },
  cohort_study:      { label: 'Cohort Study',       tier: 'amber' },
  abstract:          { label: 'Abstract',           tier: 'gray'  },
  case_report:       { label: 'Case Report',        tier: 'red'   },
  unknown:           { label: 'Reference',          tier: 'gray'  },
};

const EV_BORDER = {
  green: 'var(--ev-green-fg)',
  blue:  'var(--ev-blue-fg)',
  amber: 'var(--ev-amber-fg)',
  red:   'var(--ev-red-fg)',
  gray:  'var(--ev-gray-fg)',
};

function CopyAPA({ citation }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    const apa = `${citation.source?.toUpperCase() || 'Source'} (${citation.year}). ${citation.title}. ${citation.url || ''}`.trim();
    navigator.clipboard.writeText(apa).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button className="cite-copy-btn" onClick={copy}>
      {copied ? '✓ Copied' : 'Copy citation'}
    </button>
  );
}

function SourceCard({ c, index }) {
  const meta = EV_META[c.evidence_type] || EV_META.unknown;
  const border = EV_BORDER[meta.tier];
  const pct = c.confidence ? Math.round(c.confidence * 100) : null;

  return (
    <div
      className="source-card card-enter"
      style={{ borderLeftColor: border, animationDelay: `${index * 0.07}s` }}
    >
      <div className="sc-top">
        <div className="sc-num">{c.num}</div>
        <div className="sc-title">{c.title}</div>
      </div>
      <div className="sc-tags">
        <span className={`ev-tag ev-tag-${meta.tier}`}>{meta.label}</span>
        <span className="sc-meta">{c.source?.toUpperCase()} · {c.year}</span>
        {pct && <span className="sc-conf">{pct}%</span>}
      </div>
      {c.url && (
        <div className="sc-actions">
          <a className="sc-link" href={c.url} target="_blank" rel="noopener noreferrer">
            View source ↗
          </a>
          <CopyAPA citation={c} />
        </div>
      )}
    </div>
  );
}

export default function SourcesPanel({ citations }) {
  return (
    <aside className="sources-panel">
      <style>{`
        .sources-panel {
          background: var(--sidebar-bg);
          backdrop-filter: blur(24px);
          -webkit-backdrop-filter: blur(24px);
          border-left: 1px solid var(--border);
          padding: 1.25rem 1rem;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
          display: flex; flex-direction: column;
        }
        .sp-header { margin-bottom: 1rem; padding: 0 0.25rem; }
        .sp-eyebrow {
          font-size: 10px; font-weight: 700; color: var(--text-muted);
          text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 2px;
        }
        .sp-title {
          font-family: var(--font-display); font-size: 18px;
          font-weight: 500; color: var(--text-primary);
        }
        .sp-sub { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }

        .source-card {
          background: var(--panel-alpha); backdrop-filter: blur(12px);
          border: 1px solid var(--border-soft);
          border-left: 3px solid var(--ev-green-fg);
          border-radius: var(--radius-md);
          padding: 13px 14px; margin-bottom: 10px;
          box-shadow: var(--shadow-sm);
          transition: transform 0.16s, box-shadow 0.16s;
        }
        .source-card:hover { transform: translateX(2px); box-shadow: var(--shadow-md); }

        .sc-top { display: flex; align-items: flex-start; gap: 9px; margin-bottom: 7px; }
        .sc-num {
          width: 20px; height: 20px; border-radius: 5px;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white; font-size: 10.5px; font-weight: 700;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0; box-shadow: var(--shadow-sage);
        }
        .sc-title {
          font-size: 12.5px; font-weight: 600; color: var(--text-primary); line-height: 1.4;
        }
        .sc-tags {
          display: flex; align-items: center; gap: 6px;
          flex-wrap: wrap; margin-bottom: 8px;
        }
        .ev-tag {
          font-size: 9.5px; font-weight: 700; padding: 2px 7px;
          border-radius: 4px; text-transform: uppercase; letter-spacing: 0.04em;
        }
        .ev-tag-green { background: var(--ev-green-bg); color: var(--ev-green-fg); }
        .ev-tag-blue  { background: var(--ev-blue-bg);  color: var(--ev-blue-fg);  }
        .ev-tag-amber { background: var(--ev-amber-bg); color: var(--ev-amber-fg); }
        .ev-tag-red   { background: var(--ev-red-bg);   color: var(--ev-red-fg);   }
        .ev-tag-gray  { background: var(--ev-gray-bg);  color: var(--ev-gray-fg);  }
        .sc-meta { font-size: 11px; color: var(--text-tertiary); }
        .sc-conf {
          font-size: 10.5px; font-weight: 600; color: var(--sage);
          background: var(--sage-light); padding: 1px 6px;
          border-radius: 4px; margin-left: auto;
        }
        .sc-actions { display: flex; align-items: center; gap: 8px; }
        .sc-link {
          font-size: 11.5px; color: var(--sage); text-decoration: none; transition: color 0.14s;
        }
        .sc-link:hover { color: var(--sage-dark); text-decoration: underline; }
        .cite-copy-btn {
          font-size: 11px; color: var(--text-tertiary); background: none;
          border: 1px solid var(--border); padding: 3px 8px;
          border-radius: var(--radius-pill); transition: all 0.14s; margin-left: auto;
        }
        .cite-copy-btn:hover { border-color: var(--sage); color: var(--sage); background: var(--sage-pill); }

        .ev-legend {
          margin-top: auto; padding-top: 1rem;
          border-top: 1px solid var(--border-subtle);
        }
        .legend-title {
          font-size: 10px; font-weight: 700; color: var(--text-muted);
          text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;
        }
        .legend-row {
          display: flex; align-items: center; gap: 8px;
          margin-bottom: 5px; font-size: 11px; color: var(--text-tertiary);
        }
        .legend-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }

        .empty-state {
          flex: 1; display: flex; flex-direction: column;
          align-items: center; justify-content: center;
          text-align: center; padding: 2rem 1rem; color: var(--text-tertiary);
        }
        .empty-icon { color: var(--border); margin-bottom: 12px; }
        .empty-title {
          font-family: var(--font-display); font-size: 15px;
          color: var(--text-secondary); margin-bottom: 5px;
        }
        .empty-sub { font-size: 12px; line-height: 1.6; max-width: 22ch; margin: 0 auto; }
      `}</style>

      <div className="sp-header">
        <div className="sp-eyebrow">Evidence</div>
        <div className="sp-title">Sources</div>
        <div className="sp-sub">
          {citations.length > 0
            ? `${citations.length} reference${citations.length > 1 ? 's' : ''} for this response`
            : 'References will appear here'}
        </div>
      </div>

      {citations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" style={{ margin: '0 auto' }}>
              <rect x="8" y="5" width="20" height="28" rx="3"
                stroke="currentColor" strokeWidth="1.5"/>
              <path d="M13 13h10M13 18h10M13 23h6"
                stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="30" cy="30" r="7" fill="var(--panel-alpha)"
                stroke="currentColor" strokeWidth="1.4"/>
              <path d="M28 30h4M30 28v4"
                stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="empty-title">No sources yet</div>
          <div className="empty-sub">
            Ask a clinical question and cited sources appear here, numbered to match.
          </div>
        </div>
      ) : (
        citations.map((c, i) => <SourceCard key={c.num} c={c} index={i} />)
      )}

      {citations.length > 0 && (
        <div className="ev-legend">
          <div className="legend-title">Evidence hierarchy</div>
          {[
            { label: 'Systematic review / RCT', fg: 'var(--ev-green-fg)' },
            { label: 'Clinical trial / Guideline', fg: 'var(--ev-blue-fg)' },
            { label: 'Cohort / FDA label', fg: 'var(--ev-amber-fg)' },
            { label: 'Case report', fg: 'var(--ev-red-fg)' },
          ].map(item => (
            <div className="legend-row" key={item.label}>
              <div className="legend-dot" style={{ background: item.fg }} />
              {item.label}
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}