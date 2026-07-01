const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export async function askQuestion(question, { sourceFilter = null, minYear = null } = {}) {
  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      source_filter: sourceFilter,
      min_year: minYear,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${response.status})`);
  }

  return response.json();
}
