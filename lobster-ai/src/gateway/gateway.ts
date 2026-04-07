/**
 * The Gateway — routes messages through a 7-stage loop (OpenClaw pattern).
 *
 * 1. NORMALIZE — channel adapter already did this
 * 2. ROUTE — serialize by sessionId (prevent races)
 * 3. ASSEMBLE CONTEXT — handled by prompt-assembler in root-agent
 * 4. INFER — ADK sends to Ollama (Gemma 4 31B)
 * 5. REACT LOOP — ADK handles tool call iterations
 * 6. RESPOND — send response back through channel adapter
 * 7. PERSIST — save session history + any memories written by tools
 */
import { runAgent } from '../agent/agent-runner.js';
import { appendMessage } from './session-store.js';
import type { Channel } from '../channels/channel.interface.js';

/** Session locks — ensures only one message processes per session at a time. */
const sessionLocks = new Map<string, Promise<void>>();

async function acquireSessionLock(sessionId: string): Promise<() => void> {
  // Wait for any existing operation on this session
  while (sessionLocks.has(sessionId)) {
    await sessionLocks.get(sessionId);
  }

  let release: () => void;
  const lockPromise = new Promise<void>((resolve) => {
    release = resolve;
  });
  sessionLocks.set(sessionId, lockPromise);

  return () => {
    sessionLocks.delete(sessionId);
    release!();
  };
}

/**
 * Handle an incoming message through the 7-stage loop.
 */
export async function handleMessage(
  sessionId: string,
  text: string,
  channel: Channel,
) {
  // Stage 2: ROUTE — acquire session lock
  const releaseLock = await acquireSessionLock(sessionId);

  try {
    // Stage 1: NORMALIZE (already done by channel adapter)

    // Stage 7 (pre): PERSIST user message
    appendMessage(sessionId, 'user', text);

    // Stage 6: Send status (thinking indicator)
    channel.sendStatus(sessionId, 'thinking');

    // Stages 3-5: ASSEMBLE CONTEXT → INFER → REACT LOOP
    // (handled by ADK InMemoryRunner + prompt-assembler)
    const result = await runAgent('user', sessionId, text);

    // Stage 6: RESPOND — send tool status updates, then final response
    for (const tc of result.toolCalls) {
      channel.sendStatus(sessionId, `Used tool: ${tc.name}`);
    }

    // Stage 7: PERSIST assistant response
    appendMessage(sessionId, 'assistant', result.text);

    // Stage 6: RESPOND — send final text
    channel.sendText(sessionId, result.text);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Unknown error';
    channel.sendText(sessionId, `Error: ${errorMsg}`);
  } finally {
    releaseLock();
  }
}
