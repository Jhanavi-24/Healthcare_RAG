import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { askQuestion } from '../api/client';

const CHIPS = [
  "What's the typical starting dose?",
  "Can I take it with alcohol?",
  "Food interactions?",
  "Are there any alternatives?",
];

const WELCOME = {
  role: 'assistant',
  text: "Hello! I'm **MediChat AI** — your clinical knowledge assistant. Ask me anything about drugs, clinical guidelines, or medical literature. I'll cite my sources.",
  citations: [],
};

export default function ChatPanel({
  messages,
  setMessages,
  onCitationsUpdate,
  onFirstExchange,
  darkMode,
  onToggleDark,
}) {
  const [input, setInput] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const scrollRef = useRef(null);
  const display = messages.length === 0 ? [WELCOME] : messages;

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  async function handleSend(override) {
    const q = (override ?? input).trim();
    if (!q || isAsking) return;
    setInput('');
    const isFirst = messages.length === 0;
    setMessages(prev => [
      ...prev,
      { role: 'user', text: q },
      { role: 'assistant', loading: true },
    ]);
    setIsAsking(true);
    try {
      const data = await askQuestion(q);
      onCitationsUpdate(data.citations || []);
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'assistant',
          text: data.answer,
          citations: data.citations,
          confidence: data.confidence_score,
        };
        return next;
      });
      if (isFirst) onFirstExchange(q.slice(0, 42), data.citations?.length || 0);
    } catch (err) {
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'assistant',
          text: `I couldn't reach the knowledge base: ${err.message}. Make sure the API server is running on port 8000.`,
          citations: [],
        };
        return next;
      });
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="chat-panel">
      <style>{`
        .chat-panel {
          display: flex; flex-direction: column;
          background: transparent; min-width: 0;
        }
        .chat-header {
          display: flex; align-items: center; gap: 12px;
          padding: 0.875rem 1.5rem;
          background: var(--panel-alpha);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-radius: var(--radius-xl) var(--radius-xl) 0 0;
          margin: 1rem 1rem 0;
          box-shadow: var(--shadow-sm);
          border: 1px solid var(--border-soft);
        }
        .header-mark {
          width: 34px; height: 34px; border-radius: 10px;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white; display: flex; align-items: center; justify-content: center;
          font-family: var(--font-display); font-size: 17px; font-weight: 600;
          flex-shrink: 0;
        }
        .header-title {
          font-size: 16px; font-weight: 700; color: var(--text-primary);
          letter-spacing: -0.01em;
        }
        .header-title b { color: var(--sage); }
        .header-sub { font-size: 11px; color: var(--text-tertiary); }
        .disclaimer-badge {
          display: flex; align-items: center; gap: 6px;
          background: var(--amber-bg); border: 1px solid var(--amber-border);
          color: var(--amber-text); font-size: 11.5px; font-weight: 500;
          padding: 6px 13px; border-radius: var(--radius-pill);
          margin-left: auto; white-space: nowrap;
        }
        .header-right {
          display: flex; align-items: center; gap: 10px; margin-left: 12px;
        }
        .toggle-wrap { display: flex; align-items: center; gap: 7px; }
        .dark-toggle {
          width: 38px; height: 20px; background: var(--border-soft);
          border-radius: var(--radius-pill); border: 1px solid var(--border);
          position: relative; transition: background 0.22s;
        }
        .dark-toggle.on { background: var(--sage); border-color: var(--sage); }
        .dark-toggle::after {
          content: ''; position: absolute; top: 2px; left: 2px;
          width: 14px; height: 14px; background: white; border-radius: 50%;
          box-shadow: var(--shadow-xs);
          transition: transform 0.22s cubic-bezier(0.34,1.56,0.64,1);
        }
        .dark-toggle.on::after { transform: translateX(18px); }
        .toggle-icon { font-size: 13px; line-height: 1; }

        .chat-body {
          flex: 1;
          background: var(--panel-alpha);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid var(--border-soft);
          border-top: none;
          margin: 0 1rem;
          box-shadow: var(--shadow-sm);
          display: flex; flex-direction: column;
          overflow: hidden;
        }
        .scroll-area {
          flex: 1; overflow-y: auto;
          padding: 1.5rem 1.5rem 0.5rem;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }
        .scroll-area::-webkit-scrollbar { width: 3px; }
        .scroll-area::-webkit-scrollbar-thumb {
          background: var(--border); border-radius: 2px;
        }

        .chips-row {
          display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
          padding: 0.75rem 1.5rem;
          border-top: 1px solid var(--border-subtle);
        }
        .chips-label {
          font-size: 11.5px; color: var(--text-tertiary); font-weight: 500; flex-shrink: 0;
        }
        .chip {
          background: transparent; border: 1px solid var(--border);
          color: var(--text-secondary); font-size: 12px;
          padding: 6px 13px; border-radius: var(--radius-pill);
          transition: all 0.14s; white-space: nowrap;
        }
        .chip:hover { border-color: var(--sage); color: var(--sage); background: var(--sage-pill); }

        .input-area { padding: 0 1rem 1rem; }
        .input-row {
          display: flex; align-items: center; gap: 10px;
          background: var(--panel-raised);
          border: 1.5px solid var(--border);
          border-radius: var(--radius-pill);
          padding: 6px 8px 6px 16px;
          transition: border-color 0.18s, box-shadow 0.18s;
          box-shadow: var(--shadow-xs);
        }
        .input-row:focus-within {
          border-color: var(--sage);
          box-shadow: 0 0 0 3px var(--sage-glow);
        }
        .input-row input {
          flex: 1; background: none; border: none; outline: none;
          font-size: 14px; color: var(--text-primary); padding: 9px 0;
        }
        .input-row input::placeholder { color: var(--text-tertiary); }
        .attach-btn {
          background: none; border: none; color: var(--text-tertiary);
          display: flex; padding: 4px; border-radius: 6px;
          transition: color 0.14s, background 0.14s;
        }
        .attach-btn:hover { color: var(--sage); background: var(--sage-pill); }
        .send-btn {
          width: 36px; height: 36px; border-radius: 50%; border: none;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white; display: flex; align-items: center; justify-content: center;
          box-shadow: var(--shadow-sage);
          transition: opacity 0.15s, transform 0.12s, box-shadow 0.15s;
        }
        .send-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(58,138,110,0.4);
        }
        .send-btn:disabled { opacity: 0.3; cursor: not-allowed; box-shadow: none; }
        .send-btn:not(:disabled):active { transform: scale(0.94); }
        .input-hint {
          font-size: 10.5px; color: var(--text-muted);
          text-align: center; margin-top: 7px;
        }
        @media (max-width: 1200px) { .disclaimer-badge { display: none; } }
      `}</style>

      <div className="chat-header">
        <div className="header-mark">+</div>
        <div>
          <div className="header-title">MediChat <b>AI</b></div>
          <div className="header-sub">
            {isAsking ? 'Searching evidence base…' : 'Grounded in PubMed'}
          </div>
        </div>
        <div className="disclaimer-badge">
          <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
            <path
              d="M7 1.5l6 10.5H1L7 1.5Z"
              stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"
            />
            <path
              d="M7 5.5v3M7 10.5v.01"
              stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"
            />
          </svg>
          For informational use only — not a substitute for medical advice
        </div>
        <div className="header-right">
          <div className="toggle-wrap">
            <span className="toggle-icon">☀️</span>
            <button
              className={`dark-toggle ${darkMode ? 'on' : ''}`}
              onClick={onToggleDark}
              aria-label="Toggle dark mode"
            />
            <span className="toggle-icon">🌙</span>
          </div>
        </div>
      </div>

      <div className="chat-body">
        <div className="scroll-area" ref={scrollRef}>
          {display.map((m, i) => <MessageBubble key={i} message={m} />)}
        </div>

        {messages.length > 0 && !isAsking && (
          <div className="chips-row">
            <span className="chips-label">Suggested:</span>
            {CHIPS.map(c => (
              <button key={c} className="chip" onClick={() => handleSend(c)}>
                {c}
              </button>
            ))}
          </div>
        )}

        <div className="input-area">
          <div className="input-row">
            <button className="attach-btn" aria-label="Attach file">
              <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                <path
                  d="M8 3v10M3 8h10"
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
                />
              </svg>
            </button>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask a clinical question…"
              disabled={isAsking}
            />
            <button
              className="send-btn"
              onClick={() => handleSend()}
              disabled={isAsking || !input.trim()}
              aria-label="Send"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path
                  d="M3 8h10M9 4l4 4-4 4"
                  stroke="currentColor" strokeWidth="1.6"
                  strokeLinecap="round" strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
          <div className="input-hint">
            Press Enter to send · answers grounded in retrieved evidence
          </div>
        </div>
      </div>
    </main>
  );
}