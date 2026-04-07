/**
 * Channel adapter interface — uniform abstraction for all messaging channels.
 * Each channel (Web, Telegram, etc.) implements this to normalize/send messages.
 */
export interface Channel {
  /** Send a text response to the user. */
  sendText(sessionId: string, text: string): void;
  /** Send a status update (typing indicator, tool usage, etc.). */
  sendStatus(sessionId: string, status: string): void;
}

/** Normalized incoming message from any channel. */
export interface NormalizedMessage {
  sessionId: string;
  userId: string;
  text?: string;
  audio?: Buffer;
  audioMimeType?: string;
  channel: Channel;
}
