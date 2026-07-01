import React, { useRef, useState } from 'react';

export default function Sidebar({
  sessions, activeSessionId, onSelectSession, onNewChat,
  uploadedDocs, onDocUploaded,
}) {
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const grouped = sessions.reduce((acc, s) => {
    acc[s.group] = acc[s.group] || [];
    acc[s.group].push(s);
    return acc;
  }, {});

  function handleFiles(fileList) {
    const file = fileList?.[0];
    if (!file) return;
    onDocUploaded({
      name: file.name,
      sizeMB: (file.size / (1024 * 1024)).toFixed(1),
    });
  }

  return (
    <aside className="sidebar">
      <style>{`
        .sidebar {
          background: var(--sidebar-bg);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-right: 1px solid var(--border);
          display: flex;
          flex-direction: column;
          padding: 1.25rem 1rem;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }
        .brand {
          display: flex; align-items: center; gap: 8px;
          margin-bottom: 1.5rem; padding: 0 0.25rem;
        }
        .brand-mark {
          width: 30px; height: 30px; border-radius: 9px;
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white;
          display: flex; align-items: center; justify-content: center;
          font-size: 14px; font-weight: 700; flex-shrink: 0;
          box-shadow: 0 2px 8px rgba(61,139,114,0.4);
        }
        .brand-name { font-size: 15px; font-weight: 700; color: var(--text-primary); }
        .brand-name b { color: var(--sage); }

        .new-chat-btn {
          background: linear-gradient(135deg, var(--sage), var(--sage-dark));
          color: white; border: none;
          border-radius: var(--radius-md); padding: 12px 16px;
          font-size: 13.5px; font-weight: 600;
          display: flex; align-items: center; justify-content: center; gap: 8px;
          margin-bottom: 1.5rem;
          box-shadow: 0 2px 10px rgba(61,139,114,0.35);
          transition: opacity 0.15s, transform 0.1s;
        }
        .new-chat-btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .new-chat-btn:active { transform: translateY(0); }

        .group-label {
          font-size: 10.5px; font-weight: 700; color: var(--text-tertiary);
          text-transform: uppercase; letter-spacing: 0.08em;
          margin: 1rem 0 0.4rem 0.25rem;
        }

        .session-item {
          display: block; width: 100%; text-align: left;
          background: transparent; border: 1px solid transparent;
          border-radius: var(--radius-sm); padding: 9px 12px;
          margin-bottom: 2px; transition: all 0.12s;
        }
        .session-item:hover {
          background: var(--sage-light);
          border-color: var(--border);
        }
        .session-item.active {
          background: var(--sage-light);
          border-color: rgba(61,139,114,0.25);
        }
        .session-title {
          font-size: 13px; font-weight: 500; color: var(--text-primary);
          margin-bottom: 2px; white-space: nowrap;
          overflow: hidden; text-overflow: ellipsis;
        }
        .session-meta { font-size: 11px; color: var(--text-tertiary); }

        .sidebar-spacer { flex: 1; min-height: 1rem; }

        .upload-zone {
          border: 1.5px dashed var(--border);
          border-radius: var(--radius-md); padding: 1.25rem 1rem;
          text-align: center; cursor: pointer;
          background: transparent;
          transition: all 0.15s;
        }
        .upload-zone:hover, .upload-zone.drag-over {
          border-color: var(--sage);
          background: var(--sage-pill);
        }
        .upload-icon { color: var(--sage); margin-bottom: 6px; }
        .upload-label { font-size: 13px; font-weight: 600; color: var(--text-primary); }
        .upload-sub { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }

        .doc-item {
          display: flex; align-items: center; gap: 10px;
          background: var(--panel-alpha);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-soft);
          border-radius: var(--radius-sm);
          padding: 10px 12px; margin-top: 8px;
        }
        .doc-icon {
          width: 28px; height: 28px; border-radius: 6px;
          background: var(--sage-light); color: var(--sage-dark);
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .doc-name {
          font-size: 12.5px; font-weight: 500; color: var(--text-primary);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .doc-status {
          font-size: 11px; color: var(--sage);
          display: flex; align-items: center; gap: 4px;
        }
      `}</style>

      <div className="brand">
        <div className="brand-mark">M</div>
        <div className="brand-name">MediChat <b>AI</b></div>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
          <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/>
        </svg>
        New Chat
      </button>

      {Object.entries(grouped).map(([group, items]) => (
        <div key={group}>
          <div className="group-label">{group}</div>
          {items.map(s => (
            <button
              key={s.id}
              className={`session-item ${s.id === activeSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(s.id)}
            >
              <div className="session-title">{s.title}</div>
              <div className="session-meta">
                {s.sourceCount > 0
                  ? `${s.sourceCount} sources`
                  : 'No messages yet'}
              </div>
            </button>
          ))}
        </div>
      ))}

      <div className="sidebar-spacer" />

      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
      >
        <div className="upload-icon">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M10 13V4M10 4L6 8M10 4l4 4"
              stroke="currentColor" strokeWidth="1.6"
              strokeLinecap="round" strokeLinejoin="round"
            />
            <path
              d="M4 14v1.5A1.5 1.5 0 0 0 5.5 17h9a1.5 1.5 0 0 0 1.5-1.5V14"
              stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
            />
          </svg>
        </div>
        <div className="upload-label">Upload documents</div>
        <div className="upload-sub">PDF, DOCX, TXT</div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {uploadedDocs.map((doc, i) => (
        <div className="doc-item" key={i}>
          <div className="doc-icon">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path
                d="M4 2h6l3 3v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z"
                stroke="currentColor" strokeWidth="1.3"
              />
            </svg>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="doc-name">{doc.name}</div>
            <div className="doc-status">
              {doc.sizeMB} MB · indexed
              <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                <path
                  d="M2.5 6.5l2.2 2.2L9.5 3.5"
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>
        </div>
      ))}
    </aside>
  );
}