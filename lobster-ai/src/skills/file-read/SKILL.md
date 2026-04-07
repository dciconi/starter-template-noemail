---
name: file_read
description: Reads the contents of a file and returns it as text.
parameters:
  path:
    type: string
    description: Absolute or relative path to the file to read
    required: true
  encoding:
    type: string
    description: "File encoding (default: utf-8)"
    required: false
---

## Usage
Read file contents. Use when the user asks to see a file, inspect configuration, or needs file data for further processing.
