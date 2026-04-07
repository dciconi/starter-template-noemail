/**
 * Voice transcription using Gemma 4 E4B via Ollama.
 * Gemma 4 E4B has native audio understanding — it can accept audio input
 * and return text transcription.
 */
import OpenAI from 'openai';
import { config } from '../config.js';

const client = new OpenAI({
  baseURL: `${config.OLLAMA_BASE_URL}/v1`,
  apiKey: 'ollama',
});

/**
 * Transcribe audio using Gemma 4 E4B's native audio understanding.
 * Sends audio as base64-encoded data in a multimodal message.
 */
export async function transcribeAudio(audioBuffer: Buffer, mimeType = 'audio/webm'): Promise<string> {
  const base64Audio = audioBuffer.toString('base64');

  const response = await client.chat.completions.create({
    model: config.VOICE_MODEL,
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: 'Transcribe the following audio. Return ONLY the transcription text, nothing else.',
          },
          {
            type: 'image_url', // Ollama uses image_url for all binary data
            image_url: {
              url: `data:${mimeType};base64,${base64Audio}`,
            },
          },
        ],
      },
    ],
  });

  return response.choices[0]?.message?.content?.trim() ?? '';
}
