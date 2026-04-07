import { runAgent } from '../agent/agent-runner.js';
import { appendMessage } from './session-store.js';

export interface Channel {
  sendText(sessionId: string, text: string): void;
  sendStatus(sessionId: string, status: string): void;
}

export async function handleMessage(
  sessionId: string,
  text: string,
  channel: Channel,
) {
  appendMessage(sessionId, 'user', text);
  channel.sendStatus(sessionId, 'thinking');

  try {
    const result = await runAgent('user', sessionId, text);

    // Send tool status updates
    for (const tc of result.toolCalls) {
      channel.sendStatus(sessionId, `Used tool: ${tc.name}`);
    }

    appendMessage(sessionId, 'assistant', result.text);
    channel.sendText(sessionId, result.text);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Unknown error';
    channel.sendText(sessionId, `Error: ${errorMsg}`);
  }
}
