import { LlmAgent, LLMRegistry, FunctionTool } from '@google/adk';
import { OllamaLlm } from './ollama-llm.js';
import { assembleSystemPrompt } from './prompt-assembler.js';
import { config } from '../config.js';

// Register Ollama provider so ADK can resolve "ollama/..." model strings
LLMRegistry.register(OllamaLlm);

const modelName = config.MAIN_MODEL.startsWith('ollama/')
  ? config.MAIN_MODEL
  : `ollama/${config.MAIN_MODEL}`;

/**
 * Create the root LlmAgent with SOUL.md personality and all skills.
 * The instruction is assembled from SOUL.md + TOOLS.md + skills list + memories.
 */
export async function createRootAgent(
  skills: FunctionTool[],
  memories: string[] = [],
): Promise<LlmAgent> {
  const instruction = await assembleSystemPrompt(skills, memories);

  return new LlmAgent({
    name: 'lobster_ai',
    model: modelName,
    description: 'LobsterAI — a personal AI assistant running locally on Gemma 4',
    instruction,
    tools: skills,
  });
}
