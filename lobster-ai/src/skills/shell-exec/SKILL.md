---
name: shell_exec
description: Execute a shell command and return its output.
parameters:
  command:
    type: string
    description: The shell command to execute
    required: true
  timeout_ms:
    type: number
    description: Timeout in milliseconds (default 10000)
    required: false
---

## Usage
Run shell commands on the user's machine. Use for file operations, system queries, package management, git commands, etc.

## Safety
- Never run destructive commands without user confirmation
- Timeout defaults to 10 seconds
- Commands blocked: rm -rf /, mkfs, dd if=, fork bombs
