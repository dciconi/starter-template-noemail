import { serve } from '@hono/node-server';
import { createNodeWebSocket } from '@hono/node-ws';
import { Hono } from 'hono';
import { serveStatic } from '@hono/node-server/serve-static';
import { config } from './config.js';
import { initRunner, runAgent } from './agent/agent-runner.js';
import { loadSkills } from './skills/index.js';
import { createWSHandlers } from './channels/web/web-channel.js';
import { startTelegramBot } from './channels/telegram/telegram-channel.js';
import chalk from 'chalk';

async function main() {
  // Load skills and initialize agent
  const skills = await loadSkills();
  initRunner(skills);
  console.log(chalk.gray(`   Skills: ${skills.map((s) => s.name).join(', ')}`));

  const app = new Hono();
  const { injectWebSocket, upgradeWebSocket } = createNodeWebSocket({ app });

  // WebSocket endpoint
  app.get('/ws', upgradeWebSocket(() => createWSHandlers()));

  // Health check
  app.get('/health', (c) => c.json({ status: 'ok', model: config.MAIN_MODEL }));

  // REST chat endpoint (for testing)
  app.post('/chat', async (c) => {
    const body = await c.req.json<{ message: string; sessionId?: string }>();
    if (!body.message) return c.json({ error: 'message is required' }, 400);
    const result = await runAgent('user', body.sessionId ?? 'default', body.message);
    return c.json(result);
  });

  // Serve static files from public/
  app.use('/*', serveStatic({ root: './public' }));

  // Start server
  const server = serve({ fetch: app.fetch, port: config.PORT }, (info) => {
    console.log(chalk.bold.cyan('\n🦞 LobsterAI'));
    console.log(chalk.gray(`   Model:  ${config.MAIN_MODEL}`));
    console.log(chalk.gray(`   Ollama: ${config.OLLAMA_BASE_URL}`));
    console.log(chalk.green(`   Ready:  http://localhost:${info.port}\n`));
  });

  injectWebSocket(server);

  // Start Telegram bot if token is configured
  if (config.TELEGRAM_BOT_TOKEN) {
    startTelegramBot().catch((err) =>
      console.error('Telegram bot error:', err.message),
    );
  }
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
