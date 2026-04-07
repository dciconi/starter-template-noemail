import { InMemoryRunner, FunctionTool } from '@google/adk';
import type { Event } from '@google/adk';
import { createRootAgent } from './root-agent.js';

const APP_NAME = 'lobster_ai';

let runner: InMemoryRunner;

/** Initialize the agent runner with skills. Must be called once at startup. */
export function initRunner(skills: FunctionTool[]) {
  const agent = createRootAgent(skills);
  runner = new InMemoryRunner({
    agent,
    appName: APP_NAME,
  });
}

/** Map of userId:sessionId pairs that have been created */
const knownSessions = new Set<string>();

async function ensureSession(userId: string, sessionId: string) {
  const key = `${userId}:${sessionId}`;
  if (!knownSessions.has(key)) {
    await runner.sessionService.createSession({
      appName: APP_NAME,
      userId,
      sessionId,
    });
    knownSessions.add(key);
  }
}

export interface AgentResponse {
  text: string;
  toolCalls: Array<{ name: string; args: Record<string, unknown>; result?: unknown }>;
}

/**
 * Run a single turn of the agent and collect the response.
 */
export async function runAgent(
  userId: string,
  sessionId: string,
  message: string,
): Promise<AgentResponse> {
  if (!runner) throw new Error('Runner not initialized. Call initRunner() first.');

  await ensureSession(userId, sessionId);

  const toolCalls: AgentResponse['toolCalls'] = [];
  let finalText = '';

  for await (const event of runner.runAsync({
    userId,
    sessionId,
    newMessage: { role: 'user', parts: [{ text: message }] },
  })) {
    const e = event as Event & { isFinalResponse?: () => boolean };

    // Collect tool usage from intermediate events
    const parts = e.content?.parts ?? [];
    for (const part of parts) {
      if (part.functionCall) {
        toolCalls.push({
          name: part.functionCall.name!,
          args: (part.functionCall.args ?? {}) as Record<string, unknown>,
        });
      }
      if (part.functionResponse) {
        const lastTool = toolCalls[toolCalls.length - 1];
        if (lastTool && !lastTool.result) {
          lastTool.result = part.functionResponse.response;
        }
      }
    }

    // Capture final text response
    if (e.isFinalResponse?.()) {
      const textParts = (e.content?.parts ?? [])
        .filter((p: { text?: string }) => p.text)
        .map((p: { text?: string }) => p.text);
      finalText = textParts.join('\n');
    }
  }

  if (!finalText) {
    finalText = '(No response generated)';
  }

  return { text: finalText, toolCalls };
}
