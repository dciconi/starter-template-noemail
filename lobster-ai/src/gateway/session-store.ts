/** In-memory conversation session store with TTL and sliding window. */

interface Session {
  messages: Array<{ role: 'user' | 'assistant'; content: string }>;
  lastAccess: number;
}

const TTL_MS = 60 * 60 * 1000; // 1 hour
const MAX_MESSAGES = 50;

const sessions = new Map<string, Session>();

export function getOrCreateSession(sessionId: string): Session {
  let session = sessions.get(sessionId);
  if (!session) {
    session = { messages: [], lastAccess: Date.now() };
    sessions.set(sessionId, session);
  }
  session.lastAccess = Date.now();
  return session;
}

export function appendMessage(
  sessionId: string,
  role: 'user' | 'assistant',
  content: string,
) {
  const session = getOrCreateSession(sessionId);
  session.messages.push({ role, content });
  // Sliding window
  if (session.messages.length > MAX_MESSAGES) {
    session.messages = session.messages.slice(-MAX_MESSAGES);
  }
}

/** Periodic cleanup of expired sessions */
setInterval(() => {
  const now = Date.now();
  for (const [id, session] of sessions) {
    if (now - session.lastAccess > TTL_MS) {
      sessions.delete(id);
    }
  }
}, 5 * 60 * 1000); // every 5 minutes
