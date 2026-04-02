#!/bin/bash
mkdir -p .claude/contracts/stubs
stubgen -p app.services -p app.models --include-docstrings -o .claude/contracts/stubs/ 2>/dev/null
python -c "
from app.main import app; import json
c={'paths':app.openapi()['paths'],'schemas':app.openapi().get('components',{}).get('schemas',{})}
open('.claude/contracts/api_contract.json','w').write(json.dumps(c,indent=2))
" 2>/dev/null
echo "Contracts generated in .claude/contracts/"
