/**
 * Skill loader — discovers skill directories (each with SKILL.md + tool.ts)
 * following the OpenClaw convention.
 */
import { FunctionTool } from '@google/adk';
import { readdir, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export interface SkillMetadata {
  name: string;
  directory: string;
  hasSkillMd: boolean;
}

/**
 * Auto-discovers skill directories in src/skills/.
 * Each skill directory must contain a tool.ts that exports `tool` (a FunctionTool).
 * Optionally contains a SKILL.md with YAML frontmatter metadata.
 */
export async function loadSkills(): Promise<FunctionTool[]> {
  const tools: FunctionTool[] = [];
  const entries = await readdir(__dirname);

  for (const entry of entries) {
    const entryPath = join(__dirname, entry);
    const entryStat = await stat(entryPath).catch(() => null);
    if (!entryStat?.isDirectory()) continue;

    // Look for tool.ts or tool.js in the directory
    const toolPath = join(entryPath, 'tool.ts');
    const toolPathJs = join(entryPath, 'tool.js');

    try {
      // Try .ts first (tsx), then .js (compiled)
      let mod;
      try {
        mod = await import(toolPath);
      } catch {
        mod = await import(toolPathJs);
      }

      if (mod.tool instanceof FunctionTool) {
        tools.push(mod.tool);
      }
    } catch (err) {
      console.warn(`  Failed to load skill "${entry}":`, (err as Error).message);
    }
  }

  return tools;
}
