import React, { useRef, useState } from 'react';

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  uploadedDocs,
  onDocUploaded,
}) {
  const fileRef = useRef(null);
  const [drag, setDrag] = useState(false);
  const [search, setSearch] = useState('');

  const grouped = sessions
    .filter(s =>
      !search || s.title.toLowerCase().includes(search.toLowerCase())
    )
    .reduce((acc, s) => {
      acc[s.group] = acc[s.group] || [];
      acc[s.group].push(s);
      return acc;
    }, {});

  function handleFiles(list) {
    const f = list?.[0];
    if (f) onDocUploaded({ name: f.name, sizeMB: (f.size / 1048576).toFixed(1) });
  }

  return (
    <aside className="sidebar">
      <style>{`
        .sidebar {
          background: var(--sidebar-bg);
          backdrop-filter: blur(24px);
          -webkit-backdrop-filter: blur(24px);
          border-right: 1px solid var(--border);
          display: flex; flex-direction: column;
          padding: 1.25rem 0.875rem;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }
        .sidebar-top { padding: 0 0.25rem; margin-bottom: 1.5rem; }
        .brand { display: flex; align-items: center; gap: 10px; margin-bottom: 1.25rem; }
        .brand-mark {
          width: 32px; height: 32px; border-radius: 10px;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white; display: flex; align-items: center; justify-content: center;
          font-family: var(--font-display); font-size: 16px; font-weight: 600;
          flex-shrink: 0; box-shadow: var(--shadow-sage);
        }
        .brand-name {
          font-size: 15px; font-weight: 700; color: var(--text-primary);
          letter-spacing: -0.01em;
        }
        .brand-name b { color: var(--sage); }
        .brand-sub { font-size: 10.5px; color: var(--text-tertiary); margin-top: 1px; }

        .search-bar {
          display: flex; align-items: center; gap: 8px;
          background: var(--panel-alpha); border: 1px solid var(--border);
          border-radius: var(--radius-sm); padding: 7px 12px;
          margin-bottom: 0.875rem; transition: border-color 0.15s;
        }
        .search-bar:focus-within { border-color: var(--sage); }
        .search-bar svg { color: var(--text-tertiary); flex-shrink: 0; }
        .search-bar input {
          flex: 1; background: none; border: none; outline: none;
          font-size: 12.5px; color: var(--text-primary);
        }
        .search-bar input::placeholder { color: var(--text-tertiary); }

        .new-chat-btn {
          width: 100%;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white; border: none; border-radius: var(--radius-md);
          padding: 11px 16px; font-size: 13.5px; font-weight: 600;
          display: flex; align-items: center; justify-content: center; gap: 8px;
          box-shadow: var(--shadow-sage);
          transition: opacity 0.15s, transform 0.12s;
          letter-spacing: -0.01em;
        }
        .new-chat-btn:hover { opacity: 0.92; transform: translateY(-1px); }
        .new-chat-btn:active { transform: translateY(0); }

        .session-group { margin-top: 1rem; }
        .group-label {
          font-size: 10px; font-weight: 700; color: var(--text-muted);
          text-transform: uppercase; letter-spacing: 0.10em;
          padding: 0 0.5rem; margin-bottom: 0.375rem;
        }
        .session-item {
          display: flex; align-items: flex-start; gap: 8px;
          width: 100%; text-align: left;
          background: transparent; border: 1px solid transparent;
          border-radius: var(--radius-sm); padding: 9px 10px; margin-bottom: 1px;
          cursor: pointer; transition: all 0.14s;
        }
        .session-item:hover { background: var(--sage-light); border-color: var(--border); }
        .session-item.active {
          background: var(--sage-light);
          border-color: rgba(58,138,110,0.22);
        }
        .session-dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--sage); flex-shrink: 0; margin-top: 5px; opacity: 0;
        }
        .session-item.active .session-dot { opacity: 1; }
        .session-title {
          font-size: 12.5px; font-weight: 500; color: var(--text-primary);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.4;
        }
        .session-meta { font-size: 11px; color: var(--text-tertiary); margin-top: 1px; }

        .sidebar-spacer { flex: 1; min-height: 0.5rem; }

        .upload-section { margin-top: 0.75rem; }
        .upload-label-text {
          font-size: 10px; font-weight: 700; color: var(--text-muted);
          text-transform: uppercase; letter-spacing: 0.10em;
          padding: 0 0.5rem; margin-bottom: 0.5rem;
        }
        .upload-zone {
          border: 1.5px dashed var(--border); border-radius: var(--radius-md);
          padding: 1.1rem 1rem; text-align: center; cursor: pointer;
          background: transparent; transition: all 0.18s;
        }
        .upload-zone:hover, .upload-zone.drag {
          border-color: var(--sage); background: var(--sage-pill);
        }
        .upload-icon { color: var(--sage); margin-bottom: 5px; }
        .upload-name { font-size: 12.5px; font-weight: 600; color: var(--text-primary); }
        .upload-sub { font-size: 10.5px; color: var(--text-tertiary); margin-top: 1px; }

        .doc-item {
          display: flex; align-items: center; gap: 8px;
          background: var(--panel-alpha); border: 1px solid var(--border-soft);
          border-radius: var(--radius-sm); padding: 9px 10px; margin-top: 6px;
        }
        .doc-icon {
          width: 26px; height: 26px; border-radius: 6px;
          background: var(--sage-light); color: var(--sage-dark);
          display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        }
        .doc-name {
          font-size: 12px; font-weight: 500; color: var(--text-primary);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .doc-status {
          font-size: 10.5px; color: var(--sage);
          display: flex; align-items: center; gap: 3px; margin-top: 1px;
        }
      `}</style>

      <div className="sidebar-top">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>
            <div className="brand-name">MediChat <b>AI</b></div>
            <div className="brand-sub">Clinical knowledge assistant</div>
          </div>
        </div>
        <div className="search-bar">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.4"/>
            <path d="M11 11l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search conversations…"
          />
        </div>
        <button className="new-chat-btn" onClick={onNewChat}>
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          New Chat
        </button>
      </div>

      {Object.entries(grouped).map(([group, items]) => (
        <div className="session-group" key={group}>
          <div className="group-label">{group}</div>
          {items.map(s => (
            <button
              key={s.id}
              className={`session-item ${s.id === activeSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(s.id)}
            >
              <div className="session-dot" />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="session-title">{s.title}</div>
                <div className="session-meta">
                  {s.sourceCount > 0 ? `${s.sourceCount} sources` : 'No messages yet'}
                </div>
              </div>
            </button>
          ))}
        </div>
      ))}

      <div className="sidebar-spacer" />

      <div className="upload-section">
        <div className="upload-label-text">Documents</div>
        <div
          className={`upload-zone ${drag ? 'drag' : ''}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={e => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files); }}
        >
          <div className="upload-icon">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path
                d="M10 12V4M10 4L6.5 7.5M10 4l3.5 3.5"
                stroke="currentColor" strokeWidth="1.6"
                strokeLinecap="round" strokeLinejoin="round"
              />
              <path
                d="M4 14v1.5A1.5 1.5 0 005.5 17h9a1.5 1.5 0 001.5-1.5V14"
                stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
              />
            </svg>
          </div>
          <div className="upload-name">Upload documents</div>
          <div className="upload-sub">PDF, DOCX, TXT</div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt"
            style={{ display: 'none' }}
            onChange={e => handleFiles(e.target.files)}
          />
        </div>
        {uploadedDocs.map((doc, i) => (
          <div className="doc-item" key={i}>
            <div className="doc-icon">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                <path
                  d="M4 2h6l3 3v9a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"
                  stroke="currentColor" strokeWidth="1.3"
                />
              </svg>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="doc-name">{doc.name}</div>
              <div className="doc-status">
                {doc.sizeMB} MB · indexed
                <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
                  <path
                    d="M2 6.5l2.5 2.5 5.5-5"
                    stroke="currentColor" strokeWidth="1.5"
                    strokeLinecap="round" strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}