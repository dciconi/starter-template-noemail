import { z } from 'zod';
import { createTool } from './create-tool.js';

export const tool = createTool({
  name: 'calculator',
  description: 'Evaluates a mathematical expression. Supports +, -, *, /, **, %, parentheses, and Math functions like Math.sqrt(), Math.PI, etc.',
  parameters: z.object({
    expression: z.string().describe('The math expression to evaluate, e.g. "2 * (3 + 4)" or "Math.sqrt(144)"'),
  }),
  execute: async ({ expression }: { expression: string }) => {
    if (!/^[\d\s+\-*/().%,eE^]+$/.test(expression.replace(/Math\.\w+/g, ''))) {
      return { error: 'Invalid expression. Only numbers, operators, and Math.* functions are allowed.' };
    }
    try {
      const fn = new Function('Math', `"use strict"; return (${expression});`);
      const result = fn(Math);
      return { expression, result: Number(result) };
    } catch (err) {
      return { error: `Evaluation failed: ${(err as Error).message}` };
    }
  },
});
