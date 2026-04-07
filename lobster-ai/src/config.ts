import 'dotenv/config';
import { z } from 'zod';

const envSchema = z.object({
  OLLAMA_BASE_URL: z.string().default('http://localhost:11434'),
  MAIN_MODEL: z.string().default('gemma4:31b'),
  VOICE_MODEL: z.string().default('gemma4:e4b'),
  PORT: z.coerce.number().default(3001),
  TELEGRAM_BOT_TOKEN: z.string().optional(),
});

export const config = envSchema.parse(process.env);
