import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { askQuestion } from '../api/client';

const SUGGESTED = [
  "What's the typical starting dose?",
  "Can I take it with alcohol?",
  "Food interactions?",
];

const WELCOME = {
  role: 'assistant',
  text: "Hello! I'm **MediChat AI** — your clinical knowledge assistant. Ask me anything about drugs, clinical guidelines, or medical literature. I'll cite my sources.",
  citations: [],
};

export default function ChatPanel({
  messages, setMessages, onCitationsUpdate, onFirstExchange,
  darkMode, onToggleDark,
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

  async function handleSend(textOverride) {
    const question = (textOverride ?? input).trim();
    if (!question || isAsking) return;

    setInput('');
    const isFirst = messages.length === 0;

    setMessages(prev => [
      ...prev,
      { role: 'user', text: question },
      { role: 'assistant', loading: true },
    ]);
    setIsAsking(true);

    try {
      const data = await askQuestion(question);
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
      if (isFirst) {
        onFirstExchange(question.slice(0, 40), data.citations?.length || 0);
      }
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
          display: flex;
          flex-direction: column;
          background: transparent;
          min-width: 0;
        }
        .chat-header {
          display: flex; align-items: center; gap: 12px;
          padding: 1rem 1.5rem;
          background: var(--panel-alpha);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-radius: var(--radius-lg) var(--radius-lg) 0 0;
          margin: 1.25rem 1.25rem 0;
          box-shadow: var(--shadow-card);
          border: 1px solid var(--border-soft);
        }
        .header-mark {
          width: 36px; height: 36px; border-radius: 10px;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white;
          display: flex; align-items: center; justify-content: center;
          font-size: 18px; font-weight: 700; flex-shrink: 0;
        }
        .header-title {
          font-size: 17px; font-weight: 700; color: var(--text-primary);
        }
        .header-title b { color: var(--sage); }
        .disclaimer-badge {
          display: flex; align-items: center; gap: 6px;
          background: var(--amber-bg);
          border: 1px solid var(--amber-border);
          color: var(--amber-text);
          font-size: 12px; font-weight: 500;
          padding: 7px 14px;
          border-radius: var(--radius-pill);
          margin-left: auto;
        }
        .header-controls {
          display: flex; align-items: center; gap: 8px; margin-left: 12px;
        }
        .dark-toggle {
          width: 40px; height: 22px;
          background: var(--border);
          border-radius: var(--radius-pill);
          border: none; position: relative;
          transition: background 0.2s;
          flex-shrink: 0;
        }
        .dark-toggle.on { background: var(--sage); }
        .dark-toggle::after {
          content: '';
          position: absolute; top: 3px; left: 3px;
          width: 16px; height: 16px;
          background: white; border-radius: 50%;
          transition: transform 0.2s;
          box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .dark-toggle.on::after { transform: translateX(18px); }
        .moon-icon { font-size: 14px; color: var(--text-tertiary); }

        .chat-body {
          flex: 1;
          background: var(--panel-alpha);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid var(--border-soft);
          border-top: none;
          margin: 0 1.25rem;
          box-shadow: var(--shadow-card);
          display: flex; flex-direction: column;
          overflow: hidden;
        }
        .messages-scroll {
          flex: 1; overflow-y: auto; padding: 1.5rem;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }
        .messages-scroll::-webkit-scrollbar { width: 4px; }
        .messages-scroll::-webkit-scrollbar-thumb {
          background: var(--border); border-radius: 2px;
        }

        .suggested-row {
          display: flex; align-items: center; gap: 8px;
          flex-wrap: wrap; padding: 0 1.5rem 1rem;
        }
        .suggested-label {
          font-size: 12.5px; color: var(--text-tertiary); font-weight: 500;
        }
        .suggested-chip {
          background: transparent;
          border: 1px solid var(--border);
          color: var(--text-primary);
          font-size: 12.5px; padding: 7px 14px;
          border-radius: var(--radius-pill);
          transition: border-color 0.15s, background 0.15s;
        }
        .suggested-chip:hover {
          border-color: var(--sage);
          background: var(--sage-pill);
        }

        .input-row {
          display: flex; align-items: center; gap: 10px;
          margin: 0 1.5rem 1.5rem;
          background: var(--bg-cream);
          border: 1.5px dashed var(--border);
          border-radius: var(--radius-pill);
          padding: 6px 8px 6px 18px;
          transition: border-color 0.15s, background 0.15s;
        }
        .input-row:focus-within {
          border-color: var(--sage);
          border-style: solid;
          background: var(--panel);
        }
        .input-row input {
          flex: 1; background: none; border: none; outline: none;
          font-size: 14.5px; color: var(--text-primary); padding: 10px 0;
        }
        .input-row input::placeholder { color: var(--text-tertiary); }
        .send-btn {
          width: 38px; height: 38px; border-radius: 50%; border: none;
          background: var(--sage); color: white;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
          box-shadow: 0 2px 8px rgba(61,139,114,0.35);
          transition: background 0.15s, opacity 0.15s, transform 0.1s;
        }
        .send-btn:hover:not(:disabled) { background: var(--sage-dark); }
        .send-btn:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }
        .send-btn:not(:disabled):active { transform: scale(0.94); }

        @media (max-width: 1100px) { .disclaimer-badge { display: none; } }
      `}</style>

      <div className="chat-header">
        <div className="header-mark">+</div>
        <div className="header-title">MediChat <b>AI</b></div>
        <div className="disclaimer-badge">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
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
        <div className="header-controls">
          <button
            className={`dark-toggle ${darkMode ? 'on' : ''}`}
            onClick={onToggleDark}
            aria-label="Toggle dark mode"
          />
          <span className="moon-icon" aria-hidden="true">🌙</span>
        </div>
      </div>

      <div className="chat-body">
        <div className="messages-scroll" ref={scrollRef}>
          {display.map((m, i) => <MessageBubble key={i} message={m} />)}
        </div>

        {messages.length > 0 && !isAsking && (
          <div className="suggested-row">
            <span className="suggested-label">Suggested:</span>
            {SUGGESTED.map(s => (
              <button
                key={s}
                className="suggested-chip"
                onClick={() => handleSend(s)}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="input-row">
          <button
            style={{
              background: 'none', border: 'none',
              color: 'var(--text-tertiary)', display: 'flex',
            }}
            aria-label="Attach file"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 3v10M3 8h10"
                stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
              />
            </svg>
          </button>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask a medical question…"
            disabled={isAsking}
          />
          <button
            className="send-btn"
            onClick={() => handleSend()}
            disabled={isAsking || !input.trim()}
            aria-label="Send"
          >
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
              <path
                d="M3 8h10M9 4l4 4-4 4"
                stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </main>
  );
}