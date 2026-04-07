export interface Channel {
  sendText(sessionId: string, text: string): void;
  sendStatus(sessionId: string, status: string): void;
}
