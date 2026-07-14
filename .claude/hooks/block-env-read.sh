#!/usr/bin/env bash
# PreToolUse hook: deny Claude from viewing .env file contents.
#
# Blocks Read/Grep/Bash calls whose target references a bare ".env" path
# segment (e.g. ".env", "app/.env") while explicitly allowing lookalikes
# like ".env.example" or ".env.sample" through, since those never hold
# real secrets.
set -euo pipefail

input="$(cat)"
tool="$(jq -r '.tool_name' <<< "$input")"

case "$tool" in
  Read)
    target="$(jq -r '.tool_input.file_path // empty' <<< "$input")"
    ;;
  Grep)
    target="$(jq -r '.tool_input.path // empty' <<< "$input")"
    ;;
  Bash)
    target="$(jq -r '.tool_input.command // empty' <<< "$input")"
    ;;
  *)
    exit 0
    ;;
esac

# Matches a bare ".env" path segment: preceded by start/slash/space, and
# followed by end/slash/space/quote/pipe/semicolon/ampersand/paren — so
# ".env" is blocked but ".env.example" (followed by ".") is not.
if grep -qE '(^|[/ ])\.env([/ '"'"'"|;&)]|$)' <<< "$target"; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Blocked by project policy: .env files must not be viewed by Claude (contains secrets). Use .env.example to see the expected shape instead."
    }
  }'
fi
