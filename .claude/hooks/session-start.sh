#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

git fetch origin claude/continue-work-WfJ0X
git checkout claude/continue-work-WfJ0X
git pull origin claude/continue-work-WfJ0X

pip install -q -r requirements.txt

echo 'export PYTHONPATH="$CLAUDE_PROJECT_DIR"' >> "$CLAUDE_ENV_FILE"
