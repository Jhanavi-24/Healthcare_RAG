import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import SourcesPanel from './components/SourcesPanel';
import './index.css';

export default function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [sessions, setSessions] = useState([
    { id: 's1', title: 'New conversation', sourceCount: 0, group: 'Today' },
  ]);
  const [activeSessionId, setActiveSessionId] = useState('s1');
  const [messages, setMessages] = useState([]);
  const [activeCitations, setActiveCitations] = useState([]);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [mousePos, setMousePos] = useState({ x: 0.5, y: 0.5 });
  const rafRef = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute(
      'data-theme',
      darkMode ? 'dark' : 'light'
    );
  }, [darkMode]);

  useEffect(() => {
    const handleMove = (e) => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        setMousePos({
          x: e.clientX / window.innerWidth,
          y: e.clientY / window.innerHeight,
        });
      });
    };
    window.addEventListener('mousemove', handleMove);
    return () => window.removeEventListener('mousemove', handleMove);
  }, []);

  function startNewChat() {
    const id = `s${Date.now()}`;
    setSessions(prev => [
      { id, title: 'New conversation', sourceCount: 0, group: 'Today' },
      ...prev,
    ]);
    setActiveSessionId(id);
    setMessages([]);
    setActiveCitations([]);
  }

  function renameActiveSession(title, sourceCount) {
    setSessions(prev =>
      prev.map(s =>
        s.id === activeSessionId ? { ...s, title, sourceCount } : s
      )
    );
  }

  const ox = (mousePos.x - 0.5) * 30;
  const oy = (mousePos.y - 0.5) * 30;

  return (
    <>
      <div className="app-bg" aria-hidden="true">
        <div
          className="orb3-el"
          style={{
            top: '55%',
            left: '55%',
            transform: `translate(calc(-50% + ${ox * -0.6}px), calc(-50% + ${oy * -0.6}px))`,
          }}
        />
        <div
          className="orb4-el"
          style={{
            top: '25%',
            left: '40%',
            transform: `translate(calc(-50% + ${ox * 0.4}px), calc(-50% + ${oy * 0.4}px))`,
          }}
        />
      </div>
      <div className="noise-overlay" aria-hidden="true" />

      <div className="app-shell">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onNewChat={startNewChat}
          uploadedDocs={uploadedDocs}
          onDocUploaded={(doc) => setUploadedDocs(prev => [...prev, doc])}
        />
        <ChatPanel
          messages={messages}
          setMessages={setMessages}
          onCitationsUpdate={setActiveCitations}
          onFirstExchange={renameActiveSession}
          darkMode={darkMode}
          onToggleDark={() => setDarkMode(d => !d)}
        />
        <SourcesPanel citations={activeCitations} />
      </div>
    </>
  );
}