import React, { useState, useEffect } from 'react';
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

  // Apply data-theme to <html> so all CSS variables cascade everywhere
  useEffect(() => {
    document.documentElement.setAttribute(
      'data-theme',
      darkMode ? 'dark' : 'light'
    );
  }, [darkMode]);

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

  return (
    <>
      {/* Animated colour orbs — sit behind everything */}
      <div className="app-bg" aria-hidden="true">
        <div className="orb3" />
      </div>

      <div className="app-shell">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onNewChat={startNewChat}
          uploadedDocs={uploadedDocs}
          onDocUploaded={(doc) => setUploadedDocs(prev => [...prev, doc])}
          darkMode={darkMode}
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