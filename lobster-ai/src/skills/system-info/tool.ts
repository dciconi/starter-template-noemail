import { z } from 'zod';
import os from 'node:os';
import { createTool } from '../create-tool.js';

export const tool = createTool({
  name: 'system_info',
  description: 'Returns system information: OS, CPU, memory, uptime, hostname.',
  parameters: z.object({}),
  execute: async () => {
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    return {
      hostname: os.hostname(),
      platform: os.platform(),
      arch: os.arch(),
      os_release: os.release(),
      cpus: os.cpus().length,
      cpu_model: os.cpus()[0]?.model,
      total_memory_gb: (totalMem / 1e9).toFixed(1),
      free_memory_gb: (freeMem / 1e9).toFixed(1),
      used_memory_percent: ((1 - freeMem / totalMem) * 100).toFixed(1),
      uptime_hours: (os.uptime() / 3600).toFixed(1),
    };
  },
});
