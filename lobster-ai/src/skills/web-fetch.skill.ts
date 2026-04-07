import { z } from 'zod';
import { createTool } from './create-tool.js';

export const tool = createTool({
  name: 'web_fetch',
  description: 'Fetches a URL and returns the response body as text. Strips HTML tags for cleaner output.',
  parameters: z.object({
    url: z.string().url().describe('The URL to fetch'),
    strip_html: z.boolean().optional().describe('Strip HTML tags from response (default true)'),
  }),
  execute: async ({ url, strip_html }: { url: string; strip_html?: boolean }) => {
    try {
      const resp = await fetch(url, {
        headers: { 'User-Agent': 'LobsterAI/1.0' },
        signal: AbortSignal.timeout(15000),
      });

      if (!resp.ok) {
        return { error: `HTTP ${resp.status}: ${resp.statusText}`, url };
      }

      let text = await resp.text();

      if (strip_html !== false) {
        text = text
          .replace(/<script[\s\S]*?<\/script>/gi, '')
          .replace(/<style[\s\S]*?<\/style>/gi, '')
          .replace(/<[^>]+>/g, ' ')
          .replace(/\s+/g, ' ')
          .trim();
      }

      if (text.length > 4000) {
        text = text.slice(0, 4000) + '\n[...truncated]';
      }

      return { url, content: text, status: resp.status };
    } catch (err) {
      return { error: `Fetch failed: ${(err as Error).message}`, url };
    }
  },
});
