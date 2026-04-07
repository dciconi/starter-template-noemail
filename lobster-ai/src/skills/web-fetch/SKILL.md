---
name: web_fetch
description: Fetches a URL and returns the response body as text. Strips HTML tags for cleaner output.
parameters:
  url:
    type: string
    description: The URL to fetch
    required: true
  strip_html:
    type: boolean
    description: Strip HTML tags from response (default true)
    required: false
---

## Usage
Fetch web pages or API endpoints. Use when the user asks to check a website, fetch data from an API, or download content.

## Notes
- 15-second timeout
- Response truncated to 4000 characters
- HTML stripped by default for cleaner output
