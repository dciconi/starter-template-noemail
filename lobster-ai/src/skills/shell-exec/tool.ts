import { z } from 'zod';
import { execSync } from 'node:child_process';
import { createTool } from '../create-tool.js';

const DENIED_COMMANDS = ['rm -rf /', 'mkfs', 'dd if=', ':(){', 'fork bomb'];

export const tool = createTool({
  name: 'shell_exec',
  description: 'Executes a shell command on the local machine and returns stdout/stderr. Use for listing files, running scripts, checking processes, etc.',
  parameters: z.object({
    command: z.string().describe('The shell command to execute'),
    timeout_ms: z.number().optional().describe('Timeout in milliseconds (default 10000)'),
  }),
  execute: async ({ command, timeout_ms }: { command: string; timeout_ms?: number }) => {
    for (const denied of DENIED_COMMANDS) {
      if (command.includes(denied)) {
        return { error: `Command blocked for safety: contains "${denied}"` };
      }
    }

    try {
      const stdout = execSync(command, {
        timeout: timeout_ms ?? 10000,
        maxBuffer: 1024 * 1024,
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });
      return { stdout: stdout.trim(), exit_code: 0 };
    } catch (err: unknown) {
      const e = err as { stderr?: string; status?: number; message?: string };
      return {
        stderr: e.stderr?.trim() ?? e.message ?? 'Unknown error',
        exit_code: e.status ?? 1,
      };
    }
  },
});
