#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Fetch all remote claude/ branches
git fetch origin 'refs/heads/claude/*:refs/remotes/origin/claude/*' 2>/dev/null || true

# Pick the most recently updated claude/ branch on the remote
BRANCH=$(git for-each-ref --sort=-committerdate \
  --format='%(refname:short)' 'refs/remotes/origin/claude/*' \
  | head -1 | sed 's|^origin/||')

if [ -z "$BRANCH" ]; then
  echo "session-start: no claude/ branch found on remote, staying on current branch"
else
  echo "session-start: using branch $BRANCH"
  git checkout -B "$BRANCH" "origin/$BRANCH"
fi

pip install -q -r requirements.txt

# Install skills from repo into ~/.claude/skills/
SKILLS_SRC="$CLAUDE_PROJECT_DIR/skills"
if [ -d "$SKILLS_SRC" ]; then
  mkdir -p "$HOME/.claude/skills"
  for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    dest="$HOME/.claude/skills/$skill_name"
    mkdir -p "$dest"
    cp -r "$skill_dir"* "$dest/"
    echo "session-start: installed skill $skill_name"
  done
fi

echo 'export PYTHONPATH="$CLAUDE_PROJECT_DIR"' >> "$CLAUDE_ENV_FILE"
