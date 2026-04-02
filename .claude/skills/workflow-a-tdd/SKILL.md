---
name: workflow-a-tdd
description: |
  Four-layer TDD development workflow with physical context isolation.
  Use this skill when implementing any feature, bugfix, or story that modifies backend Python code.
  Especially important when: writing tests alongside implementation, working on scoring/mastery/search/memory services,
  or any task where test quality matters. This skill prevents facade tests by physically isolating
  the test-writer from the implementer — they cannot see each other's reasoning.
  Trigger on: "implement story", "dev this feature", "fix this bug with TDD", "write tests for",
  "implement with quality gates", "TDD cycle", "workflow A".
---

# Workflow A — Four-Layer TDD with Physical Isolation

This skill implements a development workflow that prevents the #1 cause of AI code rework:
**facade tests** (tests that mirror implementation logic instead of testing real behavior).

Research shows that when the same agent writes both tests and implementation, over 50% of
generated tests are implementation mirrors with only 57.3% mutation kill rate. Physical isolation
of the test-writer from the implementer raises this dramatically — the test-writer is forced to
write black-box tests because it literally cannot see the implementation code.

## When to use this skill

- Any backend Python feature implementation (services, endpoints, utilities)
- Bug fixes that need regression tests
- Tasks modifying ≤ 3 production files (for larger tasks, consider manual routing)
- When you want mutation-verified test quality, not just coverage

## When NOT to use this skill

- Tauri IPC / Rust commands (cannot be unit tested this way)
- React UI components (use Superpowers or GSD instead)
- 50+ file refactors (too large for isolated TDD)
- Exploratory R&D where requirements are unclear

---

## The Four Layers

```
Layer 1: TDAD Test Map — Know which tests matter BEFORE coding
Layer 2: Agent Teams — test-writer and implementer in separate contexts
Layer 3: Boundary Enforcement — test-writer cannot read implementation files
Layer 4: Mutation Gate — surviving mutants block task completion
```

## Execution Flow

### Step 0: Pre-flight Check

Before starting, verify the environment:

```bash
# Check TDAD is available
which tdad 2>/dev/null || pip install tdad

# Generate/update test dependency map
tdad analyze ./backend 2>/dev/null || echo "TDAD not available, proceeding without test map"

# Generate interface contracts for test-writer
stubgen -p app.services -p app.models --include-docstrings -o .claude/contracts/stubs/ 2>/dev/null || echo "stubgen not available"
```

If `test_map.txt` exists, read it. If not, proceed — the skill works without it but with reduced
regression protection (70% improvement lost).

### Step 1: Analyze the Task

Read the task/story description and determine:

1. **Target files**: Which production files will be modified? (must be ≤ 3)
2. **Affected tests**: `grep "{target_file}" test_map.txt` to find related tests
3. **Interface contracts**: Read `.claude/contracts/stubs/` for function signatures
4. **Current coverage**: Check if tests already exist for the target functions

If target files > 3, split the task before proceeding.

### Step 2: RED Phase — Write Failing Tests (Isolated)

Create a task for the test-writer agent:

**Task description template:**
```
You are a TDD test-writer. Your job is to write failing tests for this requirement:
[INSERT REQUIREMENT]

Constraints:
- You can ONLY read files in: tests/, .claude/contracts/, test_map.txt
- You MUST NOT read any file in backend/app/ (implementation code)
- Every assert must test a specific value (no isinstance, no len>=0)
- Import the function under test with a real import: from app.xxx import yyy
- Use conftest.py fixtures for database/external dependencies

Affected tests from test_map.txt:
[INSERT GREP RESULTS]

Interface contracts:
[INSERT RELEVANT .pyi SIGNATURES]

Write tests in: backend/tests/unit/test_{feature_name}.py
Run pytest to confirm ALL tests FAIL (RED phase).
```

**Why isolation matters here**: The test-writer doesn't know HOW the function will be implemented.
It only knows the function signature (from contracts) and what it should do (from the requirement).
This forces genuine black-box tests that verify behavior, not implementation details.

After tests are written, verify RED:
```bash
cd backend && python -m pytest tests/unit/test_{feature_name}.py -v
# ALL tests should FAIL — if any pass, the test is likely a facade
```

### Step 3: GREEN Phase — Write Minimal Implementation (Isolated)

Create a task for the implementer agent:

**Task description template:**
```
You are a TDD implementer. Failing tests exist at:
backend/tests/unit/test_{feature_name}.py

Your job:
- Read the test file to understand what behavior is expected
- Write the MINIMUM code in backend/app/ to make all tests pass
- Do NOT modify any test file
- Do NOT add features beyond what tests require
- Do NOT optimize or refactor yet

Run pytest to confirm ALL tests PASS (GREEN phase).
```

**The implementer ONLY sees**: test files + existing source code.
**The implementer NEVER sees**: the test-writer's reasoning, the requirement text, or contracts.

After implementation, verify GREEN:
```bash
cd backend && python -m pytest tests/unit/test_{feature_name}.py -v
# ALL tests should PASS
```

### Step 4: REFACTOR Phase (Optional)

In the main context (not isolated), improve code quality while keeping tests green:

```bash
# After each refactoring change:
cd backend && python -m pytest tests/ -m "not integration and not slow" -q
# Must stay GREEN
```

### Step 5: Quality Gate — Mutation Testing

Before marking the task complete, run mutation testing on changed files:

```bash
cd backend
CHANGED=$(git diff --name-only HEAD -- '*.py' | grep 'app/' | grep -v '__pycache__')

# Prefer pytest-gremlins (3-13x faster)
python -m pytest --gremlins --gremlin-targets="$CHANGED" --gremlin-cache -q 2>/dev/null

# Fallback to mutmut
mutmut run --paths-to-mutate="$CHANGED" --use-coverage --CI 2>/dev/null
```

**Interpretation:**
- 0 surviving mutants = tests are genuine (not facades)
- Surviving mutants = tests have gaps — strengthen assertions before completing

### Step 6: Regression Check

Run the full test suite to ensure no regressions:
```bash
cd backend && python -m pytest tests/ -m "not integration and not slow" -q --tb=short
```

---

## Facade Test Detection

A facade test looks like this — it passes but tests nothing real:

```python
# BAD: Facade test (tests a copy, not the real function)
class TestScoring:
    @staticmethod
    def _compute_color(score):  # ← copied from production code!
        if score >= 10: return "green"
        ...
    def test_high_score_is_green(self):
        assert self._compute_color(12) == "green"  # ← tests the copy
```

```python
# GOOD: Real test (imports and tests the actual function)
from app.services.scoring_utils import score_to_color

def test_high_score_is_green():
    assert score_to_color(12) == "green"  # ← tests real code
```

**Rules to prevent facades:**
1. Every test file must import from `app.` — never define production logic inline
2. No `@staticmethod` that replicates production behavior in test files
3. Every assert must test a concrete value (not `isinstance`, not `len >= 0`)

---

## Hook Configuration

This skill works best with these hooks in `.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/post-tool-router.sh",
        "timeout": 30000
      }]
    }],
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/stop-gate.sh",
        "timeout": 300000
      }]
    }]
  }
}
```

PostToolUse runs fast checks (pytest + vulture, <30s).
Stop hook runs mutation testing (pytest-gremlins, up to 5 min).

---

## Task Type Routing Guide

Not every task should use Workflow A. Route by task characteristics:

| Task Type | Route | Why |
|-----------|-------|-----|
| Pure function / utility | **Workflow A** | Perfect isolation, real imports work |
| Single service method | **Workflow A** | Contracts available, testable |
| FastAPI endpoint | **Workflow A** (with TestClient) | httpx.AsyncClient for testing |
| Neo4j queries | **Manual** + testcontainers | Cannot mock safely, need real DB |
| React component | **Superpowers TDD** | UI needs visual verification |
| Tauri IPC | **Manual** + E2E | Cannot unit test Rust bridge |
| 50+ file refactor | **Manual** + incremental | Too large for isolated agents |

---

## Evidence Base

- TDAD (arxiv:2603.17973): 70% regression reduction with AST test maps on SWE-bench Verified
- AgentCoder (arxiv:2312.13010): 96.3% Pass@1 with isolation vs 67% without (HumanEval)
- A/B/C comparison test: Workflow A produced 0 facade tests, 84 real assertions
- Gemini independent judge: "Workflow A is superior — physical isolation prevents facade"
- TDD prompting paradox: Generic TDD instructions WORSEN regression by 64%
