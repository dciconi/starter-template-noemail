# LobsterAI

A local-first personal AI assistant — an [OpenClaw](https://github.com/openclaw/openclaw) clone powered by **Gemma 4** running on **Ollama**, built with **Google ADK**.

## Architecture

LobsterAI mirrors OpenClaw's core architecture:

- **Single Gateway process** — one Node.js process handles all channels, sessions, and agent execution
- **7-stage agentic loop** — Normalize → Route → Assemble Context → Infer → ReAct → Respond → Persist
- **SOUL.md** — agent personality loaded into every system prompt
- **SKILL.md directories** — each skill is a directory with metadata + tool implementation
- **Memory as Markdown** — persistent memories stored in `~/.lobster-ai/memory/`
- **Channel adapters** — uniform interface for Web (WebSocket) and Telegram
- **A2A-ready** — agent card at `/.well-known/agent.json`
- **MCP-compatible** — stub ready for external MCP tool servers

### Models

| Role | Model | Size |
|------|-------|------|
| Reasoning + Tool Calling | Gemma 4 31B | ~20GB |
| Voice / STT | Gemma 4 E4B | ~5GB |

### Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | Google ADK (`@google/adk`) |
| LLM Server | Ollama (local, OpenAI-compatible API) |
| Web Server | Hono + @hono/node-server + @hono/node-ws |
| Telegram | grammY |
| Web UI | Vanilla HTML/CSS/JS (dark theme, no build step) |
| TTS | Browser SpeechSynthesis API |

## Setup

### Prerequisites

```bash
# Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull gemma4:31b    # Main reasoning (~20GB)
ollama pull gemma4:e4b    # Voice/audio STT (~5GB)
```

### Install & Run

```bash
cd lobster-ai
cp .env.example .env      # Edit if needed
pnpm install
pnpm dev                  # Starts on http://localhost:3001
```

### Telegram Bot (Optional)

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Add `TELEGRAM_BOT_TOKEN=your-token` to `.env`
3. Restart the server

## Skills

Each skill is a directory in `src/skills/` containing:
- `SKILL.md` — YAML frontmatter (name, description, parameters) + usage guide
- `tool.ts` — ADK `FunctionTool` implementation

| Skill | Description |
|-------|-------------|
| `get_datetime` | Current date/time in any timezone |
| `calculator` | Math expression evaluation |
| `system_info` | OS, CPU, memory, uptime |
| `shell_exec` | Execute shell commands |
| `file_read` | Read file contents |
| `file_write` | Create/write files |
| `web_fetch` | Fetch URLs, strip HTML |
| `memory_save` | Persist memories to disk |
| `memory_recall` | Search saved memories |

### Adding a New Skill

```bash
mkdir src/skills/my-skill
```

Create `src/skills/my-skill/SKILL.md`:
```markdown
---
name: my_skill
description: What this skill does
parameters:
  input:
    type: string
    description: Input parameter
    required: true
---

## Usage
When and how to use this skill.
```

Create `src/skills/my-skill/tool.ts`:
```typescript
import { z } from 'zod';
import { createTool } from '../create-tool.js';

export const tool = createTool({
  name: 'my_skill',
  description: 'What this skill does',
  parameters: z.object({
    input: z.string().describe('Input parameter'),
  }),
  execute: async ({ input }) => {
    return { result: `Processed: ${input}` };
  },
});
```

Skills are auto-discovered at startup.

## Project Structure

```
lobster-ai/
  SOUL.md                    # Agent personality
  TOOLS.md                   # Tool usage guide
  .well-known/agent.json     # A2A agent card
  src/
    index.ts                 # Gateway entry point
    config.ts                # Zod-validated env config
    agent/                   # ADK agent + Ollama bridge
    gateway/                 # 7-stage loop, sessions, memory
    skills/                  # SKILL.md directories
    channels/                # Web + Telegram adapters
    mcp/                     # MCP tool server loader (stub)
  public/                    # Web chat UI (dark theme)
```

## License

MIT
