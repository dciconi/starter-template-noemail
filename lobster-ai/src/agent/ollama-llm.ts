/**
 * Custom BaseLlm implementation that connects ADK to Ollama via OpenAI-compatible API.
 * Converts between Google genai Content format and OpenAI chat completion format.
 */
import { BaseLlm } from '@google/adk';
import type { LlmRequest } from '@google/adk';
import type { LlmResponse } from '@google/adk';
import type { BaseLlmConnection } from '@google/adk';
import type {
  Content,
  FunctionCall,
  FunctionDeclaration,
  Part,
} from '@google/genai';
import OpenAI from 'openai';
import type {
  ChatCompletionMessageParam,
  ChatCompletionTool,
  ChatCompletionMessageToolCall,
} from 'openai/resources/chat/completions';
import { config } from '../config.js';

// ── Genai → OpenAI converters ────────────────────────────────────────────

function genaiContentToOpenAI(contents: Content[]): ChatCompletionMessageParam[] {
  const messages: ChatCompletionMessageParam[] = [];

  for (const content of contents) {
    const role = content.role === 'model' ? 'assistant' : 'user';
    const parts = content.parts ?? [];

    // Check for function calls (model → tool_calls)
    const functionCalls = parts.filter((p): p is Part & { functionCall: FunctionCall } => !!p.functionCall);
    const functionResponses = parts.filter((p) => !!p.functionResponse);
    const textParts = parts.filter((p) => !!p.text);

    if (functionCalls.length > 0) {
      const toolCalls: ChatCompletionMessageToolCall[] = functionCalls.map((p) => ({
        id: p.functionCall!.id ?? `call_${p.functionCall!.name}`,
        type: 'function' as const,
        function: {
          name: p.functionCall!.name!,
          arguments: JSON.stringify(p.functionCall!.args ?? {}),
        },
      }));

      messages.push({
        role: 'assistant',
        content: textParts.map((p) => p.text).join('\n') || null,
        tool_calls: toolCalls,
      });
    } else if (functionResponses.length > 0) {
      for (const p of functionResponses) {
        messages.push({
          role: 'tool',
          tool_call_id: p.functionResponse!.id ?? `call_${p.functionResponse!.name}`,
          content: JSON.stringify(p.functionResponse!.response ?? {}),
        });
      }
    } else {
      const text = textParts.map((p) => p.text).join('\n');
      messages.push({ role, content: text || '' } as ChatCompletionMessageParam);
    }
  }

  return messages;
}

function genaiToolsToOpenAI(config?: LlmRequest['config']): ChatCompletionTool[] | undefined {
  const tools = config?.tools;
  if (!tools || tools.length === 0) return undefined;

  const result: ChatCompletionTool[] = [];
  for (const tool of tools) {
    const decls = (tool as { functionDeclarations?: FunctionDeclaration[] }).functionDeclarations;
    if (!decls) continue;
    for (const decl of decls) {
      result.push({
        type: 'function',
        function: {
          name: decl.name!,
          description: decl.description ?? '',
          parameters: (decl.parameters ?? { type: 'object', properties: {} }) as Record<string, unknown>,
        },
      });
    }
  }

  return result.length > 0 ? result : undefined;
}

// ── OpenAI → Genai converters ────────────────────────────────────────────

function openAIResponseToGenai(
  choice: OpenAI.Chat.Completions.ChatCompletion.Choice,
): LlmResponse {
  const msg = choice.message;
  const parts: Part[] = [];

  if (msg.content) {
    parts.push({ text: msg.content });
  }

  if (msg.tool_calls && msg.tool_calls.length > 0) {
    for (const tc of msg.tool_calls) {
      let args: Record<string, unknown> = {};
      try {
        args = JSON.parse(tc.function.arguments);
      } catch {
        args = {};
      }
      parts.push({
        functionCall: {
          id: tc.id,
          name: tc.function.name,
          args,
        },
      });
    }
  }

  return {
    content: {
      role: 'model',
      parts,
    },
    turnComplete: true,
  };
}

// ── OllamaLlm class ─────────────────────────────────────────────────────

export class OllamaLlm extends BaseLlm {
  private client: OpenAI;

  static readonly supportedModels: Array<string | RegExp> = [
    /^ollama\/.*/,
  ];

  constructor({ model }: { model: string }) {
    // Strip "ollama/" prefix for the actual Ollama model name
    super({ model });
    this.client = new OpenAI({
      baseURL: `${config.OLLAMA_BASE_URL}/v1`,
      apiKey: 'ollama',
    });
  }

  /** The actual model name to send to Ollama (without ollama/ prefix) */
  private get ollamaModel(): string {
    return this.model.replace(/^ollama\//, '');
  }

  async *generateContentAsync(
    llmRequest: LlmRequest,
    stream = false,
  ): AsyncGenerator<LlmResponse, void> {
    const messages = genaiContentToOpenAI(llmRequest.contents);

    // Add system instruction if present
    const systemInstruction = llmRequest.config?.systemInstruction;
    if (systemInstruction) {
      let sysText = '';
      if (typeof systemInstruction === 'string') {
        sysText = systemInstruction;
      } else if (Array.isArray(systemInstruction)) {
        // PartUnion[] — each item is a Part or string
        sysText = systemInstruction
          .map((p) => (typeof p === 'string' ? p : (p as Part).text ?? ''))
          .join('\n');
      } else {
        // Content object
        sysText = ((systemInstruction as Content).parts ?? [])
          .map((p) => (typeof p === 'string' ? p : p.text ?? ''))
          .join('\n');
      }
      if (sysText) {
        messages.unshift({ role: 'system', content: sysText });
      }
    }

    const tools = genaiToolsToOpenAI(llmRequest.config);

    if (stream) {
      const streamResponse = await this.client.chat.completions.create({
        model: this.ollamaModel,
        messages,
        tools,
        stream: true,
      });

      let contentText = '';
      const toolCalls: Map<number, { id: string; name: string; args: string }> = new Map();

      for await (const chunk of streamResponse) {
        const delta = chunk.choices[0]?.delta;
        if (!delta) continue;

        if (delta.content) {
          contentText += delta.content;
          yield {
            content: { role: 'model', parts: [{ text: contentText }] },
            partial: true,
          };
        }

        if (delta.tool_calls) {
          for (const tc of delta.tool_calls) {
            const existing = toolCalls.get(tc.index) ?? { id: '', name: '', args: '' };
            if (tc.id) existing.id = tc.id;
            if (tc.function?.name) existing.name = tc.function.name;
            if (tc.function?.arguments) existing.args += tc.function.arguments;
            toolCalls.set(tc.index, existing);
          }
        }
      }

      // Yield final response
      const parts: Part[] = [];
      if (contentText) parts.push({ text: contentText });
      for (const [, tc] of toolCalls) {
        let args: Record<string, unknown> = {};
        try { args = JSON.parse(tc.args); } catch { args = {}; }
        parts.push({
          functionCall: { id: tc.id, name: tc.name, args },
        });
      }

      yield {
        content: { role: 'model', parts },
        turnComplete: true,
      };
    } else {
      const response = await this.client.chat.completions.create({
        model: this.ollamaModel,
        messages,
        tools,
        stream: false,
      });

      yield openAIResponseToGenai(response.choices[0]);
    }
  }

  async connect(_llmRequest: LlmRequest): Promise<BaseLlmConnection> {
    throw new Error('Live/streaming connections not supported for Ollama');
  }
}
