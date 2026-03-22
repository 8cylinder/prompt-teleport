# Prompt Project - Complete Index

## Quick Navigation

### I Want To...

**Understand the current issues in the code**
- Read: [CODE_REVIEW.md](CODE_REVIEW.md) - 13 issues identified and prioritized

**Learn how the tests work**
- Read: [TESTING.md](TESTING.md) - Complete testing guide
- Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common pytest commands

**See the test results**
- Read: [TEST_RESULTS.md](TEST_RESULTS.md) - Detailed test execution report
- Run: `.venv/bin/pytest tests/ -v`

**Fix a bug with test guidance**
- Read: [IMPROVEMENT_WORKFLOW.md](IMPROVEMENT_WORKFLOW.md) - Step-by-step examples
- Follow the workflow for each issue

**Understand the architecture**
- Read: [CLAUDE.md](CLAUDE.md) - High-level architecture for AI assistants

**Get the project setup**
- Read: [README.md](README.md) - Installation and usage instructions

**Run tests**
- See: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands

---

## Document Map

### Core Documentation

| Document | Purpose | For Whom |
|----------|---------|----------|
| [CODE_REVIEW.md](CODE_REVIEW.md) | Analysis of 13 code issues | Developers fixing bugs |
| [TEST_RESULTS.md](TEST_RESULTS.md) | Test execution report & findings | Project managers, QA |
| [TESTING.md](TESTING.md) | Complete testing guide | QA, CI/CD engineers |
| [IMPROVEMENT_WORKFLOW.md](IMPROVEMENT_WORKFLOW.md) | Step-by-step bug fix examples | Developers |
| [TEST_SETUP_SUMMARY.md](TEST_SETUP_SUMMARY.md) | Overview of test suite | Onboarding new contributors |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Common commands cheat sheet | Everyone |
| [CLAUDE.md](CLAUDE.md) | AI assistant configuration | Claude Code users |
| [README.md](README.md) | Project setup & usage | New users |

---

## Test Suite Status

✅ **ALL 93 TESTS PASSING** (100% pass rate)

- 27 utility function tests
- 24 project management tests
- 23 prompt generation tests
- 19 CLI integration tests

Execution time: 0.17 seconds

---

## Known Issues

The test suite has identified 4 critical/high-priority bugs:

| # | Issue | Severity | Location | Test |
|---|-------|----------|----------|------|
| 1 | Type incompatibility | CRITICAL | src/prompt/prompt.py:340-342 | test_apply_theme_* |
| 2 | Unused variables | HIGH | src/prompt/prompt.py:634,642 | ruff check |
| 3 | Path prefix bug | HIGH | src/prompt/projects.py:55 | test_path_prefix_issue |
| 4 | Invalid hex handling | MEDIUM | src/prompt/prompt.py:197 | test_scale_invalid_hex |

See [CODE_REVIEW.md](CODE_REVIEW.md) for detailed analysis and fixes.

---

## Development Workflow

### When Starting Work

```bash
# Update from repo
git pull

# Install/update dependencies
uv sync

# Run tests to establish baseline
.venv/bin/pytest tests/ -v

# Should see: 93 passed
```

### When Making Changes

**Before each change:**
```bash
.venv/bin/pytest tests/ -v      # Baseline
```

**After each change:**
```bash
.venv/bin/pytest tests/ -v      # Verify no regressions
.venv/bin/ruff check src/       # Check style
.venv/bin/mypy src/             # Check types
```

**Follow the workflow:**
1. Read [IMPROVEMENT_WORKFLOW.md](IMPROVEMENT_WORKFLOW.md) for that issue
2. Make the code change
3. Run tests to verify
4. Check linting and types
5. Commit when all tests pass

---

## Documentation Structure

### For Understanding Issues
1. [TEST_RESULTS.md](TEST_RESULTS.md) - Overview of what was found
2. [CODE_REVIEW.md](CODE_REVIEW.md) - Detailed analysis
3. [IMPROVEMENT_WORKFLOW.md](IMPROVEMENT_WORKFLOW.md) - How to fix

### For Using Tests
1. [TESTING.md](TESTING.md) - Complete guide
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands
3. Run: `.venv/bin/pytest tests/ -v` - Execute tests

### For Architecture
1. [CLAUDE.md](CLAUDE.md) - High-level overview
2. [README.md](README.md) - Getting started
3. Code files - Implementation details

---

## Key Commands

### Run Tests
```bash
# All tests
.venv/bin/pytest tests/ -v

# By category
.venv/bin/pytest tests/ -m unit -v
.venv/bin/pytest tests/ -m edge_case -v
.venv/bin/pytest tests/ -m integration -v

# Single test file
.venv/bin/pytest tests/test_prompt_utils.py -v

# With coverage
.venv/bin/pytest tests/ --cov=src/prompt --cov-report=html
```

### Code Quality
```bash
# Linting
.venv/bin/ruff check src/

# Type checking
.venv/bin/mypy src/

# All checks
.venv/bin/pytest tests/ -v && .venv/bin/ruff check src/ && .venv/bin/mypy src/
```

---

## Files in This Project

### Source Code
- `src/prompt/__init__.py` - Package entry point
- `src/prompt/prompt.py` - Prompt generation logic (734 lines)
- `src/prompt/projects.py` - Project management (273 lines)
- `src/prompt/ui.py` - CLI interface (154 lines)

### Tests
- `tests/conftest.py` - Test fixtures
- `tests/test_prompt_utils.py` - 27 utility tests
- `tests/test_projects.py` - 24 project tests
- `tests/test_chunks.py` - 23 prompt tests
- `tests/test_cli.py` - 19 CLI tests

### Configuration
- `pyproject.toml` - Project metadata & dependencies
- `pytest.ini` - Pytest configuration
- `.python-version` - Python 3.13

### Documentation
- `README.md` - Installation and usage
- `CODE_REVIEW.md` - Code analysis (13 issues)
- `TEST_RESULTS.md` - Test execution report
- `TESTING.md` - Testing guide
- `IMPROVEMENT_WORKFLOW.md` - Bug fix examples
- `TEST_SETUP_SUMMARY.md` - Test suite overview
- `QUICK_REFERENCE.md` - Command cheat sheet
- `CLAUDE.md` - AI assistant guide
- `INDEX.md` - This file

---

## Getting Help

### Questions About Tests?
→ Read [TESTING.md](TESTING.md)

### Can't figure out how to fix a bug?
→ Read [IMPROVEMENT_WORKFLOW.md](IMPROVEMENT_WORKFLOW.md) for examples

### What are the issues in the code?
→ Read [CODE_REVIEW.md](CODE_REVIEW.md)

### Quick command syntax?
→ Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### How do I run the project?
→ Read [README.md](README.md)

---

## Summary

✅ **93 tests** - All passing
✅ **4 issues identified** - Documented with fixes
✅ **Complete documentation** - For all scenarios
✅ **Ready for development** - Test-driven improvements

**Next step:** Start with [CODE_REVIEW.md](CODE_REVIEW.md) to understand the issues, then follow [IMPROVEMENT_WORKFLOW.md](IMPROVEMENT_WORKFLOW.md) to fix them.
