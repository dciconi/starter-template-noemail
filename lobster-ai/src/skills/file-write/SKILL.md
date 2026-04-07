---
name: file_write
description: Writes content to a file. Creates the file and parent directories if they do not exist.
parameters:
  path:
    type: string
    description: Absolute or relative path to the file to write
    required: true
  content:
    type: string
    description: The content to write to the file
    required: true
---

## Usage
Create or overwrite files. Use when the user asks to create a file, save output, or generate content to disk.

## Safety
- Creates parent directories automatically
- Overwrites existing files without warning — confirm with user for important files
