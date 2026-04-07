# LobsterAI

OpenClaw-inspired personal AI assistant powered by **Gemma 4** running locally via Ollama, built on **Google ADK**.

## Features

- **Chat** — Web UI + REST API + Telegram bot
- **Tools** — Shell exec, file read/write, web fetch, calculator, datetime, system info
- **Voice** — Gemma 4 E4B for STT, browser SpeechSynthesis for TTS
- **Skills** — Auto-discovered `*.skill.ts` plugins (ADK FunctionTool)
- **100% Local** — All inference runs on your machine via Ollama

## Quick Start

### Prerequisites

1. Install [Ollama](https://ollama.ai)
2. Pull models:
   ```bash
   ollama pull gemma4:31b    # Main reasoning (~20GB)
   ollama pull gemma4:e4b    # Voice/STT (~5GB)
   ```

### Run

```bash
cp .env.example .env
pnpm install
pnpm dev
```

Open **http://localhost:3001** to chat.

### Telegram (optional)

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Add `TELEGRAM_BOT_TOKEN=your_token` to `.env`
3. Restart the server

## Architecture

| Component | Technology |
|---|---|
| Agent framework | Google ADK (`@google/adk`) |
| Main model | Gemma 4 31B via Ollama |
| Voice/STT model | Gemma 4 E4B via Ollama |
| Web server | Hono + WebSocket |
| Telegram | grammY |
| TTS | Browser SpeechSynthesis |

## Adding Skills

Create a `src/skills/my-skill.skill.ts` file:

```typescript
import { z } from 'zod';
import { createTool } from './create-tool.js';

export const tool = createTool({
  name: 'my_skill',
  description: 'What this skill does',
  parameters: z.object({
    input: z.string().describe('Description for the model'),
  }),
  execute: async ({ input }) => {
    return { result: `Processed: ${input}` };
  },
});
```

Skills are auto-discovered at startup.
