import { FunctionTool } from '@google/adk';

/**
 * Wrapper around FunctionTool constructor to avoid Zod version mismatch
 * between project's zod and ADK's expected zod types.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function createTool(options: any): FunctionTool {
  return new FunctionTool(options);
}
