# Tool Usage Guide

## When to Use Tools

Use tools proactively when the user's request requires real-time data or system interaction.
Don't guess — verify with tools.

## Tool Decision Heuristics

| User wants... | Use tool... |
|---|---|
| Current time or date | `get_datetime` |
| Math calculation | `calculator` |
| System info (CPU, RAM, OS) | `system_info` |
| Run a command | `shell_exec` |
| Read a file | `file_read` |
| Create or modify a file | `file_write` |
| Fetch a webpage or API | `web_fetch` |
| Remember something | `memory_save` |
| Recall a past fact | `memory_recall` |

## Safety Rules

1. **shell_exec**: Always explain what command you'll run and why before executing
2. **file_write**: Confirm before overwriting existing files
3. **shell_exec**: Never run commands that delete data without explicit user confirmation
4. **web_fetch**: Respect rate limits and only fetch URLs the user provides or clearly needs

## Chaining Tools

You can chain multiple tools in one turn. For example:
- Read a config file → parse it → run a command based on its contents
- Fetch a URL → extract data → save it to a file
- Check system info → recommend actions based on available resources
