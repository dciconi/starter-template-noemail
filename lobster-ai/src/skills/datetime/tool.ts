import { z } from 'zod';
import { createTool } from '../create-tool.js';

export const tool = createTool({
  name: 'get_datetime',
  description: 'Returns the current date, time, and timezone.',
  parameters: z.object({
    timezone: z.string().optional().describe('IANA timezone like "America/New_York". Defaults to system timezone.'),
  }),
  execute: async ({ timezone }: { timezone?: string }) => {
    const opts: Intl.DateTimeFormatOptions = {
      dateStyle: 'full',
      timeStyle: 'long',
      timeZone: timezone || undefined,
    };
    return {
      datetime: new Date().toLocaleString('en-US', opts),
      iso: new Date().toISOString(),
      timezone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
    };
  },
});
