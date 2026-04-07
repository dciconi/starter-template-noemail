---
name: memory_recall
description: Search saved memories by keyword. Returns matching memories from previous sessions.
parameters:
  query:
    type: string
    description: Keywords to search for in saved memories
    required: true
  limit:
    type: number
    description: Maximum number of memories to return (default 5)
    required: false
---

## Usage
Recall previously saved information. Use when the user references something from a past conversation, asks about their preferences, or when you need context about their setup.

## Notes
- Searches across all saved memory files
- Returns the most relevant matches
