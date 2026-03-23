#!/bin/bash
# Stop hook: remind Claude to update TODO.md after completing work
if [ -f "$CLAUDE_PROJECT_DIR/TODO.md" ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"REMINDER: Check TODO.md — if any task was completed in this session, update it to [x] and commit the change."}}'
fi
