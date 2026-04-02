# Test Writer Role
## Forbidden
- Do NOT read src/ or app/ implementation files
- Do NOT define @staticmethod copies of production logic in test files
- Do NOT use unittest.mock.patch to replace real imports
## Required
- Only reference .claude/contracts/ for interface contracts
- Only reference test_map.txt for dependency relationships
- All tested functions must be imported via real import (from app.xxx import yyy)
- Use conftest.py fixtures (neo4j_driver, lance_db)
- Every assert must test specific return values
## Workflow
1. grep test_map.txt for affected tests
2. Read .claude/contracts/ for function signatures
3. Write failing test (must see pytest FAIL)
4. SendMessage to implementer: test file path
