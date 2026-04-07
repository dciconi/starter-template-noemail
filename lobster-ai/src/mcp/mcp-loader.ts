/**
 * MCP Tool Loader — loads external MCP servers as ADK tools.
 * Uses ADK's McpToolset to integrate MCP-compatible tool servers.
 *
 * This is a stub for future MCP integration. To use:
 * 1. Configure MCP servers in .env or config
 * 2. Each server provides tools that get added to the agent's tool list
 *
 * Example usage:
 *   import { McpToolset } from '@google/adk';
 *
 *   const mcpTools = new McpToolset({
 *     connectionParams: {
 *       serverName: 'filesystem',
 *       command: 'npx',
 *       args: ['-y', '@anthropic/mcp-server-filesystem', '/home/user'],
 *     },
 *   });
 *
 *   // Add to agent tools alongside skill FunctionTools
 *   agent.tools.push(mcpTools);
 */

import type { BaseToolset } from '@google/adk';

export interface McpServerConfig {
  name: string;
  command: string;
  args: string[];
}

/**
 * Load MCP servers from configuration.
 * Returns an empty array when no MCP servers are configured.
 * Future: parse MCP_SERVERS env var or config file.
 */
export async function loadMcpToolsets(
  _servers: McpServerConfig[] = [],
): Promise<BaseToolset[]> {
  // MCP integration ready — uncomment when McpToolset is needed:
  //
  // const { McpToolset } = await import('@google/adk');
  // return servers.map(
  //   (s) =>
  //     new McpToolset({
  //       connectionParams: {
  //         serverName: s.name,
  //         command: s.command,
  //         args: s.args,
  //       },
  //     }),
  // );

  return [];
}
