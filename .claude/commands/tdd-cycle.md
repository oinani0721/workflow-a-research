---
name: tdd-cycle
description: TDD Red-Green-Refactor cycle using Agent Teams physical isolation
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Agent
---

# TDD Cycle (Agent Teams Version)

Create an agent team for TDD with physical context isolation:

## Team Structure
- **test-writer** (uses test-writer agent definition): writes failing tests
- **implementer** (uses implementer agent definition): writes minimal implementation

## Task Flow
1. Create Task 1 (assign to test-writer):
   - Read the current requirement
   - Write failing tests in backend/tests/
   - Run pytest to confirm RED (tests fail)
   - Mark task as done when tests are written and confirmed failing

2. Create Task 2 (assign to implementer, blockedBy: Task 1):
   - Read the test files written by test-writer
   - Write minimal implementation in backend/app/
   - Run pytest to confirm GREEN (all tests pass)
   - Mark task as done

## Key Constraints
- test-writer MUST NOT modify backend/app/ files
- implementer MUST NOT modify backend/tests/ files
- Task 2 blockedBy ensures implementer waits for test-writer
