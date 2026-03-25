#!/usr/bin/env bash
# Fires after a Read tool call. If the file read was handoff.md,
# inject a reminder to ask the two start-of-session checklist questions.

FILE=$(jq -r '.tool_input.file_path // ""' 2>/dev/null)

case "$FILE" in
  *handoff.md)
    jq -n '{
      "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "The user just read handoff.md. Before doing anything else, ask them these two questions:\n1. Should I bump the version in src/version.py? (check current value first)\n2. Should this session'\''s changes be tracked in the changelog?"
      }
    }'
    ;;
esac
