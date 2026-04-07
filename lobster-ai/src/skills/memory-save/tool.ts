import { z } from 'zod';
import { createTool } from '../create-tool.js';
import { saveMemory } from '../../gateway/memory-store.js';

export const tool = createTool({
  name: 'memory_save',
  description: 'Save a memory that persists across sessions. Use to remember user preferences, project details, or important context.',
  parameters: z.object({
    title: z.string().describe('A short descriptive title for the memory'),
    content: z.string().describe('The content to remember'),
  }),
  execute: async ({ title, content }: { title: string; content: string }) => {
    try {
      const filename = await saveMemory(title, content);
      return { saved: true, filename, title };
    } catch (err) {
      return { error: `Failed to save memory: ${(err as Error).message}` };
    }
  },
});
