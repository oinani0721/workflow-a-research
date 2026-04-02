#!/bin/bash
# post-tool-router.sh — Lightweight PostToolUse hook
# Only runs pytest + vulture (< 30s). Mutation testing moved to Stop hook.

set -euo pipefail
PAYLOAD=$(cat)
FILE_PATH=$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')
[ -z "$FILE_PATH" ] && exit 0

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if [[ "$FILE_PATH" == *"backend/app/"* ]] || [[ "$FILE_PATH" == *"backend/tests/"* ]]; then
    cd "$PROJECT_ROOT/backend"
    python -m pytest tests/ -m "not integration and not slow" -q --tb=short --timeout=10 2>&1 | tail -20
    [ $? -ne 0 ] && echo "TEST FAILURES" >&2 && exit 2
    if [[ "$FILE_PATH" == *"backend/app/"* ]]; then
        python -m vulture app/ --min-confidence 100 2>&1 || true
    fi
fi

exit 0
