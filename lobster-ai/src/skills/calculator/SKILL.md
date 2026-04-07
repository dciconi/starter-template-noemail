---
name: calculator
description: Evaluates a mathematical expression. Supports +, -, *, /, **, %, parentheses, and Math functions.
parameters:
  expression:
    type: string
    description: "The math expression to evaluate, e.g. \"2 * (3 + 4)\" or \"Math.sqrt(144)\""
    required: true
---

## Usage
Evaluate mathematical expressions. Supports basic arithmetic, exponentiation, modulo, and JavaScript Math functions (Math.sqrt, Math.PI, Math.sin, etc.).

## Safety
- Only numbers, operators, and Math.* functions are allowed
- No arbitrary code execution
