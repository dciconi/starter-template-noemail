import type { WSContext, WSMessageReceive } from 'hono/ws';
import type { Channel } from '../channel.interface.js';
import { handleMessage } from '../../gateway/gateway.js';
import { transcribeAudio } from '../../agent/voice-agent.js';
import { nanoid } from 'nanoid';

/** Maps sessionId → WebSocket connection */
const connections = new Map<string, WSContext>();

export function createWebChannel(): Channel {
  return {
    sendText(sessionId: string, text: string) {
      const ws = connections.get(sessionId);
      if (ws) ws.send(JSON.stringify({ type: 'message', text }));
    },
    sendStatus(sessionId: string, status: string) {
      const ws = connections.get(sessionId);
      if (ws) ws.send(JSON.stringify({ type: 'status', text: status }));
    },
  };
}

const channel = createWebChannel();

/** Returns WSEvents handlers for Hono's upgradeWebSocket */
export function createWSHandlers() {
  return {
    onOpen(_event: Event, ws: WSContext) {
      const sessionId = nanoid(12);
      // Store sessionId on the ws context's raw property for retrieval
      (ws as WSContext & { _sessionId?: string })._sessionId = sessionId;
      connections.set(sessionId, ws);
      ws.send(JSON.stringify({ type: 'session', sessionId }));
    },

    onMessage(event: MessageEvent<WSMessageReceive>, ws: WSContext) {
      const sessionId = (ws as WSContext & { _sessionId?: string })._sessionId;
      if (!sessionId) return;

      // Handle binary audio data
      if (event.data instanceof ArrayBuffer || event.data instanceof Buffer) {
        const audioBuffer = Buffer.from(event.data as ArrayBuffer);
        channel.sendStatus(sessionId, 'Transcribing audio...');
        transcribeAudio(audioBuffer)
          .then((text) => {
            if (text) {
              // Echo the transcription back to the client
              const conn = connections.get(sessionId);
              if (conn) conn.send(JSON.stringify({ type: 'transcription', text }));
              handleMessage(sessionId, text, channel);
            } else {
              channel.sendText(sessionId, 'Could not transcribe audio. Please try again.');
            }
          })
          .catch(() => {
            channel.sendText(sessionId, 'Audio transcription failed. Is the voice model running?');
          });
        return;
      }

      try {
        const data = JSON.parse(String(event.data));
        if (data.type === 'message' && data.text) {
          handleMessage(sessionId, data.text, channel);
        }
        if (data.type === 'audio' && data.audio) {
          // Base64-encoded audio from client
          const audioBuffer = Buffer.from(data.audio, 'base64');
          channel.sendStatus(sessionId, 'Transcribing audio...');
          transcribeAudio(audioBuffer, data.mimeType ?? 'audio/webm')
            .then((text) => {
              if (text) {
                const conn = connections.get(sessionId);
                if (conn) conn.send(JSON.stringify({ type: 'transcription', text }));
                handleMessage(sessionId, text, channel);
              } else {
                channel.sendText(sessionId, 'Could not transcribe audio.');
              }
            })
            .catch(() => {
              channel.sendText(sessionId, 'Audio transcription failed.');
            });
        }
      } catch {
        // Ignore malformed messages
      }
    },

    onClose(_event: CloseEvent, ws: WSContext) {
      const sessionId = (ws as WSContext & { _sessionId?: string })._sessionId;
      if (sessionId) connections.delete(sessionId);
    },
  };
}
