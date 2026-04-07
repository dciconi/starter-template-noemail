import { z } from 'zod';
import { createTool } from '../create-tool.js';
import { recallMemories } from '../../gateway/memory-store.js';

export const tool = createTool({
  name: 'memory_recall',
  description: 'Search saved memories by keyword. Returns matching memories from previous sessions.',
  parameters: z.object({
    query: z.string().describe('Keywords to search for in saved memories'),
    limit: z.number().optional().describe('Maximum number of memories to return (default 5)'),
  }),
  execute: async ({ query, limit }: { query: string; limit?: number }) => {
    try {
      const memories = await recallMemories(query, limit ?? 5);
      if (memories.length === 0) {
        return { found: false, message: 'No matching memories found.' };
      }
      return { found: true, count: memories.length, memories };
    } catch (err) {
      return { error: `Failed to recall memories: ${(err as Error).message}` };
    }
  },
});
