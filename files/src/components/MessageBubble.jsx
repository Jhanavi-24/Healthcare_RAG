import React, { useState } from 'react';

function renderRich(text) {
  const lines = text.split('\n').filter(l => l.trim());
  const blocks = [];
  let buf = [];

  function flush() {
    if (buf.length) { blocks.push({ type: 'list', items: [...buf] }); buf = []; }
  }

  for (const line of lines) {
    const t = line.trim();
    if (t.startsWith('- ') || t.startsWith('• ')) { buf.push(t.slice(2)); }
    else { flush(); blocks.push({ type: 'p', text: t }); }
  }
  flush();

  function inline(str, kp) {
    return str.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((p, i) => {
      if (/^\*\*[^*]+\*\*$/.test(p)) {
        return <strong key={`${kp}-${i}`}>{p.slice(2, -2)}</strong>;
      }
      const m = p.match(/^\[(\d+)\]$/);
      if (m) {
        return <sup key={`${kp}-${i}`} className="cite-badge">{m[1]}</sup>;
      }
      return <React.Fragment key={`${kp}-${i}`}>{p}</React.Fragment>;
    });
  }

  return blocks.map((b, i) =>
    b.type === 'list' ? (
      <ul className="msg-list" key={i}>
        {b.items.map((item, ii) => <li key={ii}>{inline(item, `${i}-${ii}`)}</li>)}
      </ul>
    ) : (
      <p className="msg-p" key={i}>{inline(b.text, i)}</p>
    )
  );
}

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button className="copy-btn" onClick={copy} title="Copy response">
      {copied ? (
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
          <path d="M2 7.5l3 3 7-7" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ) : (
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
          <rect x="5" y="1" width="8" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3"/>
          <path d="M3 4H2a1 1 0 00-1 1v7a1 1 0 001 1h7a1 1 0 001-1v-1"
            stroke="currentColor" strokeWidth="1.3"/>
        </svg>
      )}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

function ConfidenceRing({ score }) {
  if (score == null) return null;
  const pct = Math.round(score * 100);
  const r = 14;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  const color = pct >= 85
    ? 'var(--ev-green-fg)'
    : pct >= 70
    ? 'var(--ev-blue-fg)'
    : pct >= 55
    ? 'var(--ev-amber-fg)'
    : 'var(--ev-red-fg)';
  const label = pct >= 85 ? 'High' : pct >= 70 ? 'Moderate' : pct >= 55 ? 'Low' : 'Very low';
  return (
    <div className="conf-ring-wrap" title={`${label} confidence (${pct}%)`}>
      <svg width="34" height="34" viewBox="0 0 34 34">
        <circle cx="17" cy="17" r={r} stroke="var(--border)" strokeWidth="2.5" fill="none"/>
        <circle cx="17" cy="17" r={r} stroke={color} strokeWidth="2.5" fill="none"
          strokeDasharray={`${dash} ${circ}`}
          strokeDashoffset={circ * 0.25}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
        <text x="17" y="21" textAnchor="middle" fontSize="8"
          fontWeight="700" fill={color}>{pct}%</text>
      </svg>
      <span className="conf-label" style={{ color }}>{label}</span>
    </div>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (isUser) {
    return (
      <div className="row row-user msg-enter">
        <style>{`
          .row { display: flex; margin-bottom: 1.5rem; gap: 10px; }
          .row-user { justify-content: flex-end; }
          .bubble-user {
            background: linear-gradient(135deg, var(--user-bubble-from), var(--user-bubble-to));
            color: var(--user-text); font-size: 14px; line-height: 1.6;
            padding: 13px 18px; border-radius: 18px 18px 4px 18px;
            max-width: 65%; box-shadow: var(--shadow-sage);
          }
          .msg-ts {
            font-size: 10.5px; color: var(--text-muted);
            opacity: 0; transition: opacity 0.2s; align-self: flex-end;
          }
          .row:hover .msg-ts { opacity: 1; }
        `}</style>
        <div className="bubble-user">{message.text}</div>
        <span className="msg-ts">{ts}</span>
      </div>
    );
  }

  return (
    <div className="row row-ai msg-enter">
      <style>{`
        .row-ai { justify-content: flex-start; align-items: flex-start; }
        .avatar {
          width: 30px; height: 30px; border-radius: 50%;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white; display: flex; align-items: center; justify-content: center;
          font-family: var(--font-display); font-size: 13px; font-weight: 600;
          flex-shrink: 0; box-shadow: var(--shadow-sage); margin-top: 2px;
        }
        .bubble-ai-wrap { max-width: 80%; }
        .bubble-ai {
          background: var(--panel-alpha); backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid var(--border-soft); font-size: 14px; line-height: 1.75;
          padding: 16px 18px; border-radius: 4px 18px 18px 18px;
          color: var(--text-primary); box-shadow: var(--shadow-sm);
        }
        .bubble-loading { display: flex; gap: 4px; align-items: center; padding: 18px; }
        .dot {
          width: 5px; height: 5px; border-radius: 50%; background: var(--text-tertiary);
          animation: dotPulse 1.4s infinite ease-in-out;
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes dotPulse {
          0%,60%,100% { transform: scale(1); opacity: 0.4; }
          30% { transform: scale(1.4); opacity: 1; }
        }
        .msg-p { margin-bottom: 0.5rem; }
        .msg-p:last-child { margin-bottom: 0; }
        .msg-list { margin: 0.4rem 0 0.6rem 1rem; }
        .msg-list li { margin-bottom: 6px; }
        .cite-badge {
          display: inline-flex; align-items: center; justify-content: center;
          background: var(--sage-light); color: var(--sage-dark);
          font-size: 9.5px; font-weight: 700; font-family: var(--font-sans);
          width: 16px; height: 16px; border-radius: 4px;
          margin: 0 1.5px; vertical-align: super;
          border: 1px solid rgba(58,138,110,0.18);
        }
        .bubble-footer {
          display: flex; align-items: center; gap: 10px;
          margin-top: 10px; flex-wrap: wrap;
        }
        .copy-btn {
          display: inline-flex; align-items: center; gap: 5px;
          background: transparent; border: 1px solid var(--border);
          color: var(--text-tertiary); font-size: 11.5px; font-weight: 500;
          padding: 4px 10px; border-radius: var(--radius-pill); transition: all 0.15s;
        }
        .copy-btn:hover { border-color: var(--sage); color: var(--sage); background: var(--sage-pill); }
        .conf-ring-wrap { display: flex; align-items: center; gap: 5px; }
        .conf-label { font-size: 11px; font-weight: 500; }
        .msg-ts { font-size: 10.5px; color: var(--text-muted); margin-left: auto; opacity: 0; transition: opacity 0.2s; }
        .row:hover .msg-ts { opacity: 1; }
      `}</style>

      <div className="avatar">M</div>
      <div className="bubble-ai-wrap">
        {message.loading ? (
          <div className="bubble-ai bubble-loading">
            <div className="dot" />
            <div className="dot" />
            <div className="dot" />
          </div>
        ) : (
          <>
            <div className="bubble-ai">{renderRich(message.text)}</div>
            <div className="bubble-footer">
              <ConfidenceRing score={message.confidence} />
              <CopyBtn text={message.text} />
              <span className="msg-ts">{ts}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}