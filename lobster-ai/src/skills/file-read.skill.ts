import { z } from 'zod';
import { readFile } from 'node:fs/promises';
import { createTool } from './create-tool.js';

export const tool = createTool({
  name: 'file_read',
  description: 'Reads the contents of a file and returns it as text.',
  parameters: z.object({
    path: z.string().describe('Absolute or relative path to the file to read'),
    encoding: z.string().optional().describe('File encoding (default "utf-8")'),
  }),
  execute: async ({ path, encoding }: { path: string; encoding?: string }) => {
    try {
      const content = await readFile(path, { encoding: (encoding ?? 'utf-8') as BufferEncoding });
      return { path, content, size: content.length };
    } catch (err) {
      return { error: `Failed to read file: ${(err as Error).message}` };
    }
  },
});
