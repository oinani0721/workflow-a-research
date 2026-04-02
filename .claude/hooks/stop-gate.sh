#!/bin/bash
# stop-gate.sh — Stop hook: mutation testing quality gate
# exit 2 = block Agent from stopping

set -uo pipefail
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

cd "$PROJECT_ROOT/backend" 2>/dev/null || exit 0

# Phase 1: Full unit tests
echo "Running full test suite..." >&2
if ! python -m pytest tests/ -m "not integration and not slow" -q --tb=short 2>&1 | tail -30; then
    echo "STOP BLOCKED: Tests failing" >&2
    exit 2
fi

# Phase 2: Mutation testing on changed files only
CHANGED=$(cd "$PROJECT_ROOT" && git diff --name-only HEAD 2>/dev/null | grep '\.py$' | grep 'backend/app/' | grep -v '__pycache__' || true)
[ -z "$CHANGED" ] && exit 0

echo "Mutation testing on: $CHANGED" >&2
TARGETS=$(echo "$CHANGED" | sed "s|backend/||" | tr '\n' ',' | sed 's/,$//')

# Prefer pytest-gremlins, fallback to mutmut
if python -m pytest --co -q --gremlins 2>/dev/null | head -1 | grep -q "gremlins"; then
    python -m pytest --gremlins --gremlin-targets="$TARGETS" --gremlin-cache -q 2>&1 || {
        echo "Mutants survived - strengthen tests" >&2; exit 2
    }
elif command -v mutmut &>/dev/null; then
    for FILE in $CHANGED; do
        REL=$(echo "$FILE" | sed 's|backend/||')
        mutmut run --paths-to-mutate="$REL" --CI --no-progress 2>&1 | tail -5
        SURV=$(mutmut results 2>/dev/null | grep -c "Survived" || echo "0")
        [ "$SURV" -gt 0 ] && echo "$SURV mutants survived" >&2 && exit 2
    done
fi

echo "All quality gates passed" >&2
exit 0
