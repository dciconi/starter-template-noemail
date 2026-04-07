import { LlmAgent, LLMRegistry, FunctionTool } from '@google/adk';
import { OllamaLlm } from './ollama-llm.js';
import { config } from '../config.js';

// Register our Ollama provider so ADK can resolve "ollama/..." model strings
LLMRegistry.register(OllamaLlm);

const modelName = config.MAIN_MODEL.startsWith('ollama/')
  ? config.MAIN_MODEL
  : `ollama/${config.MAIN_MODEL}`;

export function createRootAgent(skills: FunctionTool[]): LlmAgent {
  return new LlmAgent({
    name: 'lobster_ai',
    model: modelName,
    description: 'LobsterAI — a personal AI assistant running locally on Gemma 4',
    instruction: `You are LobsterAI, a helpful personal AI assistant running entirely on the user's local machine via Gemma 4.
You have access to tools that let you interact with the user's computer — shell commands, file operations, web fetching, and more.
When using a tool, briefly explain what you're about to do and why.
Be concise, friendly, and practical. Use markdown formatting in your responses.`,
    tools: skills,
  });
}
