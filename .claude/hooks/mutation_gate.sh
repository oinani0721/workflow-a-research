#!/bin/bash
CHANGED=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep '\.py$' | grep -v 'test_')
[ -z "$CHANGED" ] && exit 0
echo "Running mutation testing..." >&2
if python -m pytest --gremlins --gremlin-parallel --gremlin-workers=4 --gremlin-paths="$CHANGED" 2>/dev/null; then
    exit 0
fi
if command -v mutmut &>/dev/null; then
    mutmut run --paths-to-mutate "$CHANGED" --CI 2>&1
    SURVIVORS=$(mutmut results 2>/dev/null | grep -c "Survived" || echo "0")
    [ "$SURVIVORS" -gt 0 ] && echo "$SURVIVORS mutants survived" >&2 && exit 2
fi
exit 0
