import React from 'react';

function renderRichText(text) {
  const lines = text.split('\n').filter(l => l.trim() !== '');
  const blocks = [];
  let bulletBuffer = [];

  function flushBullets() {
    if (bulletBuffer.length > 0) {
      blocks.push({ type: 'list', items: bulletBuffer });
      bulletBuffer = [];
    }
  }

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      bulletBuffer.push(trimmed.slice(2));
    } else {
      flushBullets();
      blocks.push({ type: 'p', text: trimmed });
    }
  }
  flushBullets();

  function inline(str, keyPrefix) {
    const parts = str.split(/(\*\*[^*]+\*\*|\[\d+\])/g);
    return parts.map((part, i) => {
      if (/^\*\*[^*]+\*\*$/.test(part)) {
        return <b key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</b>;
      }
      const citeMatch = part.match(/^\[(\d+)\]$/);
      if (citeMatch) {
        return (
          <sup key={`${keyPrefix}-${i}`} className="cite-pill">
            {citeMatch[1]}
          </sup>
        );
      }
      return (
        <React.Fragment key={`${keyPrefix}-${i}`}>{part}</React.Fragment>
      );
    });
  }

  return blocks.map((block, bi) => {
    if (block.type === 'list') {
      return (
        <ul className="msg-list" key={bi}>
          {block.items.map((item, ii) => (
            <li key={ii}>{inline(item, `${bi}-${ii}`)}</li>
          ))}
        </ul>
      );
    }
    return (
      <p className="msg-para" key={bi}>
        {inline(block.text, bi)}
      </p>
    );
  });
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="row row-user">
        <style>{`
          .row { display: flex; margin-bottom: 1.5rem; gap: 10px; }
          .row-user { justify-content: flex-end; }
          .bubble-user {
            background: linear-gradient(135deg, var(--sage), var(--sage-dark));
            color: var(--user-text);
            font-size: 14.5px; line-height: 1.55;
            padding: 14px 18px;
            border-radius: 16px 16px 4px 16px;
            max-width: 65%;
            box-shadow: 0 2px 12px rgba(61,139,114,0.3);
          }
        `}</style>
        <div className="bubble-user">{message.text}</div>
      </div>
    );
  }

  return (
    <div className="row row-ai">
      <style>{`
        .row-ai { justify-content: flex-start; align-items: flex-start; }
        .avatar {
          width: 32px; height: 32px; border-radius: 50%;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white;
          display: flex; align-items: center; justify-content: center;
          font-size: 13px; font-weight: 700; flex-shrink: 0;
          box-shadow: 0 1px 6px rgba(61,139,114,0.35);
        }
        .bubble-ai-wrap { max-width: 78%; }
        .bubble-ai {
          background: var(--panel-alpha);
          backdrop-filter: blur(10px);
          border: 1px solid var(--border-soft);
          font-size: 14.5px; line-height: 1.7;
          padding: 16px 18px;
          border-radius: 4px 16px 16px 16px;
          color: var(--text-primary);
        }
        .bubble-ai.loading {
          display: flex; gap: 5px; align-items: center; padding: 18px;
        }
        .dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--text-tertiary);
          animation: bounce 1.2s infinite ease-in-out;
        }
        .dot:nth-child(2) { animation-delay: 0.15s; }
        .dot:nth-child(3) { animation-delay: 0.3s; }
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-4px); opacity: 1; }
        }
        .msg-para { margin-bottom: 0.5rem; }
        .msg-para:last-child { margin-bottom: 0; }
        .msg-list { margin: 0.4rem 0 0.6rem 1.1rem; }
        .msg-list li { margin-bottom: 7px; line-height: 1.6; }
        .cite-pill {
          display: inline-flex;
          align-items: center; justify-content: center;
          background: var(--sage-light);
          color: var(--sage-dark);
          font-size: 10px; font-weight: 700;
          width: 17px; height: 17px;
          border-radius: 5px;
          margin: 0 1px;
          vertical-align: super;
          border: 1px solid rgba(61,139,114,0.2);
        }
        .citecount-row {
          display: flex; align-items: center; gap: 8px;
          margin-top: 10px; padding-left: 2px;
          font-size: 12px; color: var(--text-tertiary);
        }
        .citecount-row input { accent-color: var(--sage); }
      `}</style>

      <div className="avatar">M</div>
      <div className="bubble-ai-wrap">
        {message.loading ? (
          <div className="bubble-ai loading">
            <div className="dot" />
            <div className="dot" />
            <div className="dot" />
          </div>
        ) : (
          <>
            <div className="bubble-ai">
              {renderRichText(message.text)}
            </div>
            {message.citations?.length > 0 && (
              <label className="citecount-row">
                <input type="checkbox" disabled />
                {message.citations.length} source
                {message.citations.length > 1 ? 's' : ''} cited
              </label>
            )}
          </>
        )}
      </div>
    </div>
  );
}