import { Bot } from 'grammy';
import type { Channel } from '../channel.interface.js';
import { handleMessage } from '../../gateway/gateway.js';
import { config } from '../../config.js';

let bot: Bot | null = null;

/** Pending responses keyed by chatId */
const pendingResponses = new Map<string, { resolve: (text: string) => void }>();

function createTelegramChannel(): Channel {
  return {
    sendText(sessionId: string, text: string) {
      if (!bot) return;
      const chatId = sessionId.replace('tg:', '');
      // Escape markdown v2 special characters
      const escaped = escapeMarkdownV2(text);
      bot.api.sendMessage(Number(chatId), escaped, { parse_mode: 'MarkdownV2' }).catch(() => {
        // Fallback: send as plain text if markdown parsing fails
        bot!.api.sendMessage(Number(chatId), text).catch(() => {});
      });
    },
    sendStatus(sessionId: string, status: string) {
      if (!bot) return;
      const chatId = sessionId.replace('tg:', '');
      bot.api.sendChatAction(Number(chatId), 'typing').catch(() => {});
    },
  };
}

function escapeMarkdownV2(text: string): string {
  // Split by code blocks first to avoid escaping inside them
  const parts = text.split(/(```[\s\S]*?```|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (i % 2 === 1) return part; // code blocks, leave as-is
    return part.replace(/([_*[\]()~>#+\-=|{}.!\\])/g, '\\$1');
  }).join('');
}

export async function startTelegramBot() {
  if (!config.TELEGRAM_BOT_TOKEN) return;

  bot = new Bot(config.TELEGRAM_BOT_TOKEN);
  const channel = createTelegramChannel();

  bot.command('start', (ctx) => {
    ctx.reply('👋 Hi! I\'m LobsterAI, your personal AI assistant powered by Gemma 4. Send me a message!');
  });

  bot.on('message:text', (ctx) => {
    const sessionId = `tg:${ctx.chat.id}`;
    handleMessage(sessionId, ctx.message.text, channel);
  });

  await bot.start({
    onStart: () => {
      console.log('   Telegram bot started');
    },
  });
}
