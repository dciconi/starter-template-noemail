---
name: get_datetime
description: Returns the current date, time, and timezone.
parameters:
  timezone:
    type: string
    description: IANA timezone like "America/New_York". Defaults to system timezone.
    required: false
---

## Usage
Get the current date and time. Use when the user asks what time it is, what today's date is, or needs time-related information.

## Notes
- Supports any IANA timezone string
- Returns both human-readable and ISO 8601 formats
