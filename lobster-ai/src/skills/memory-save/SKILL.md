---
name: memory_save
description: Save a memory that persists across sessions. Use to remember user preferences, project details, or important context.
parameters:
  title:
    type: string
    description: A short descriptive title for the memory
    required: true
  content:
    type: string
    description: The content to remember
    required: true
---

## Usage
Save important information that should persist across conversations. Examples:
- User preferences ("prefers dark theme", "uses pnpm")
- Project context ("main project is in /home/user/myapp, uses Next.js")
- Instructions ("always respond in French")

## Notes
- Saved as Markdown files in ~/.lobster-ai/memory/
- Proactively save things the user mentions that seem worth remembering
