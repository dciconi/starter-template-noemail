import { z } from 'zod';
import { writeFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
import { createTool } from '../create-tool.js';

export const tool = createTool({
  name: 'file_write',
  description: 'Writes content to a file. Creates the file and parent directories if they do not exist.',
  parameters: z.object({
    path: z.string().describe('Absolute or relative path to the file to write'),
    content: z.string().describe('The content to write to the file'),
  }),
  execute: async ({ path, content }: { path: string; content: string }) => {
    try {
      await mkdir(dirname(path), { recursive: true });
      await writeFile(path, content, 'utf-8');
      return { path, bytes_written: Buffer.byteLength(content) };
    } catch (err) {
      return { error: `Failed to write file: ${(err as Error).message}` };
    }
  },
});
