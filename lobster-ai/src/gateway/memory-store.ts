/**
 * Persistent memory store — saves and retrieves memories as Markdown files.
 * Mirrors OpenClaw's memory system: everything stored in ~/.lobster-ai/memory/
 */
import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { homedir } from 'node:os';

const MEMORY_DIR = join(homedir(), '.lobster-ai', 'memory');

/** Ensure the memory directory exists. */
async function ensureDir(): Promise<void> {
  await mkdir(MEMORY_DIR, { recursive: true });
}

/** Slugify a title for use as a filename. */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);
}

/** Save a memory to disk as a Markdown file. */
export async function saveMemory(title: string, content: string): Promise<string> {
  await ensureDir();
  const date = new Date().toISOString().slice(0, 10);
  const slug = slugify(title);
  const filename = `${date}_${slug}.md`;
  const filepath = join(MEMORY_DIR, filename);

  const md = `# ${title}\n\n${content}\n\n---\n_Saved: ${new Date().toISOString()}_\n`;
  await writeFile(filepath, md, 'utf-8');
  return filename;
}

/** Search memories by keyword (simple substring match across all files). */
export async function recallMemories(query: string, limit = 5): Promise<string[]> {
  await ensureDir();
  const results: Array<{ filename: string; content: string; score: number }> = [];

  let files: string[];
  try {
    files = await readdir(MEMORY_DIR);
  } catch {
    return [];
  }

  const queryLower = query.toLowerCase();
  const queryWords = queryLower.split(/\s+/).filter(Boolean);

  for (const file of files) {
    if (!file.endsWith('.md')) continue;
    try {
      const content = await readFile(join(MEMORY_DIR, file), 'utf-8');
      const contentLower = content.toLowerCase();

      // Score: number of query words found in the content
      const score = queryWords.reduce(
        (acc, word) => acc + (contentLower.includes(word) ? 1 : 0),
        0,
      );

      if (score > 0) {
        results.push({ filename: file, content, score });
      }
    } catch {
      // Skip unreadable files
    }
  }

  // Sort by score descending, take top N
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, limit).map((r) => {
    // Extract first line (title) and a snippet
    const lines = r.content.split('\n').filter(Boolean);
    const title = lines[0]?.replace(/^#+\s*/, '') ?? r.filename;
    const snippet = lines.slice(1, 3).join(' ').slice(0, 200);
    return `${title}: ${snippet}`;
  });
}

/** List all saved memory files. */
export async function listMemories(): Promise<string[]> {
  await ensureDir();
  try {
    const files = await readdir(MEMORY_DIR);
    return files.filter((f) => f.endsWith('.md'));
  } catch {
    return [];
  }
}
