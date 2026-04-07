/**
 * Assembles the system prompt from SOUL.md + TOOLS.md + skills list + memories.
 * Mirrors OpenClaw's Stage 3 (Assemble Context).
 */
import { readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { FunctionTool } from '@google/adk';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..', '..');

let cachedSoul = '';
let cachedTools = '';

async function loadMd(filename: string): Promise<string> {
  try {
    return await readFile(join(PROJECT_ROOT, filename), 'utf-8');
  } catch {
    return '';
  }
}

/** Load SOUL.md and TOOLS.md once (cached after first call). */
async function loadStaticPrompts(): Promise<void> {
  if (!cachedSoul) cachedSoul = await loadMd('SOUL.md');
  if (!cachedTools) cachedTools = await loadMd('TOOLS.md');
}

/** Build a compact skills summary (name + description only, not full schemas). */
function buildSkillsList(skills: FunctionTool[]): string {
  if (skills.length === 0) return '';
  const lines = skills.map((s) => `- **${s.name}**: ${s.description}`);
  return `## Available Tools\n\n${lines.join('\n')}`;
}

/**
 * Assemble the full system instruction for the root agent.
 * Components (in order):
 *   1. SOUL.md — personality and values
 *   2. TOOLS.md — tool usage guide
 *   3. Compact skills list — names and descriptions
 *   4. Recalled memories — persistent context from previous sessions
 */
export async function assembleSystemPrompt(
  skills: FunctionTool[],
  memories: string[] = [],
): Promise<string> {
  await loadStaticPrompts();

  const parts: string[] = [];

  if (cachedSoul) parts.push(cachedSoul);
  if (cachedTools) parts.push(cachedTools);

  const skillsList = buildSkillsList(skills);
  if (skillsList) parts.push(skillsList);

  if (memories.length > 0) {
    parts.push(
      `## Recalled Memories\n\nThese are things you've remembered from previous conversations:\n\n${memories.map((m) => `- ${m}`).join('\n')}`,
    );
  }

  return parts.join('\n\n---\n\n');
}

/** Force reload of SOUL.md and TOOLS.md (useful after edits). */
export function invalidateCache(): void {
  cachedSoul = '';
  cachedTools = '';
}
