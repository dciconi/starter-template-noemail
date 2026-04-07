import { FunctionTool } from '@google/adk';
import { readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Auto-discovers all *.skill.ts files in this directory and returns their FunctionTool exports.
 */
export async function loadSkills(): Promise<FunctionTool[]> {
  const tools: FunctionTool[] = [];
  const files = await readdir(__dirname);

  for (const file of files) {
    if (!file.endsWith('.skill.ts') && !file.endsWith('.skill.js')) continue;

    try {
      const mod = await import(join(__dirname, file));
      if (mod.tool instanceof FunctionTool) {
        tools.push(mod.tool);
      }
    } catch (err) {
      console.warn(`Failed to load skill ${file}:`, (err as Error).message);
    }
  }

  return tools;
}
