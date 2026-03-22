# Quick Reference: Test Commands

## Running Tests

```bash
# Run all tests
.venv/bin/pytest tests/ -v

# Run tests in watch mode (requires pytest-watch)
ptw tests/ -- -v

# Run with coverage report
.venv/bin/pytest tests/ --cov=src/prompt --cov-report=html

# Run specific test file
.venv/bin/pytest tests/test_prompt_utils.py -v

# Run specific test class
.venv/bin/pytest tests/test_prompt_utils.py::TestHexToRgb -v

# Run single test
.venv/bin/pytest tests/test_prompt_utils.py::TestHexToRgb::test_valid_hex_with_hash -v

# Run tests with short output
.venv/bin/pytest tests/ -q

# Run tests with detailed output
.venv/bin/pytest tests/ -vv

# Run only tests that match a pattern
.venv/bin/pytest tests/ -k "hex_to_rgb" -v

# Run tests but stop at first failure
.venv/bin/pytest tests/ -x -v
```

## Running by Category (Using Markers)

```bash
# Only unit tests (fast)
.venv/bin/pytest tests/ -m unit -v

# Only edge case tests
.venv/bin/pytest tests/ -m edge_case -v

# Only integration tests
.venv/bin/pytest tests/ -m integration -v

# Everything except integration tests
.venv/bin/pytest tests/ -m "not integration" -v
```

## Code Quality Checks

```bash
# Type checking
.venv/bin/mypy src/

# Linting and style
.venv/bin/ruff check src/

# Auto-format code
.venv/bin/ruff format src/

# Full test + lint + type check
.venv/bin/pytest tests/ -v && .venv/bin/mypy src/ && .venv/bin/ruff check src/
```

## Test Coverage

```bash
# Generate HTML coverage report
.venv/bin/pytest tests/ --cov=src/prompt --cov-report=html

# View coverage in terminal (missing lines)
.venv/bin/pytest tests/ --cov=src/prompt --cov-report=term-missing

# Coverage for specific file
.venv/bin/pytest tests/ --cov=src/prompt/prompt.py --cov-report=term
```

## Finding Tests

```bash
# List all available tests
.venv/bin/pytest tests/ --collect-only

# List tests matching a pattern
.venv/bin/pytest tests/ --collect-only -q | grep hex_to_rgb

# Show test names without running
.venv/bin/pytest tests/ --collect-only -q
```

## Debugging Tests

```bash
# Show full print output during tests
.venv/bin/pytest tests/ -v -s

# Stop at first failure with debugging info
.venv/bin/pytest tests/ -x -vv --tb=long

# Show local variables in tracebacks
.venv/bin/pytest tests/ -l -v

# Interactive debugging (drop into pdb on failure)
.venv/bin/pytest tests/ --pdb -v
```

## Common Workflows

### Before Making Changes
```bash
# Run baseline - should have 89 passing
.venv/bin/pytest tests/ -v
```

### After Making Changes
```bash
# Quick check
.venv/bin/pytest tests/ -q

# Detailed check with coverage
.venv/bin/pytest tests/ -v --cov=src/prompt

# Full validation
.venv/bin/pytest tests/ -v && .venv/bin/mypy src/ && .venv/bin/ruff check src/
```

### Fixing a Specific Bug
```bash
# 1. Run the test that demonstrates the bug
.venv/bin/pytest tests/test_projects.py::TestGetProjectDir::test_path_prefix_issue -vv

# 2. Make your fix to the code
# ... edit src/prompt/projects.py ...

# 3. Run the test again
.venv/bin/pytest tests/test_projects.py::TestGetProjectDir::test_path_prefix_issue -v

# 4. Run related tests
.venv/bin/pytest tests/test_projects.py::TestGetProjectDir -v

# 5. Run full suite to check for regressions
.venv/bin/pytest tests/ -v
```

## Test Files Reference

| File | Tests | Purpose |
|------|-------|---------|
| `test_prompt_utils.py` | 27 | Color, math, string utilities |
| `test_projects.py` | 24 | Project management, config I/O |
| `test_chunks.py` | 23 | Prompt generation, theming |
| `test_cli.py` | 19 | CLI command integration |

## Expected Test Failures (Intentional)

These 4 tests fail and reveal bugs to fix:

1. `test_scale_invalid_hex` - colorscale() error handling
2. `test_path_prefix_issue` - Path comparison bug
3. `test_multiple_projects_selects_closest` - Consequence of #2
4. `test_project_cd_no_args` - CLI expectation

See CODE_REVIEW.md for details on how to fix them.

## Documentation Files

| File | Purpose |
|------|---------|
| `CODE_REVIEW.md` | Detailed analysis of 13 issues |
| `TESTING.md` | Complete testing guide |
| `IMPROVEMENT_WORKFLOW.md` | Step-by-step fix examples |
| `TEST_SETUP_SUMMARY.md` | Overview of test suite |
| `QUICK_REFERENCE.md` | This file - common commands |

## Useful Pytest Plugins

Already installed:
- `pytest-cov` - Coverage reporting

Optional (install if needed):
```bash
# Watch mode
uv pip install pytest-watch
ptw tests/ -- -v

# Better test output
uv pip install pytest-sugar

# HTML reports
uv pip install pytest-html
.venv/bin/pytest tests/ --html=report.html
```

## Environment Variables for Testing

```bash
# Run with all warnings shown
PYTHONWARNINGS=all .venv/bin/pytest tests/ -v

# Run in strict mode
PYTHONSTRICT=1 .venv/bin/pytest tests/ -v

# Verbose import tracing
PYTHONVERBOSE=2 .venv/bin/pytest tests/ -v
```

## If Tests Fail

1. **Check the error message**
   ```bash
   .venv/bin/pytest tests/failing_test.py -vv
   ```

2. **See what changed**
   ```bash
   git diff src/
   ```

3. **Check the test expectations**
   ```bash
   grep -A 10 "def test_name" tests/test_file.py
   ```

4. **Run with more detail**
   ```bash
   .venv/bin/pytest tests/failing_test.py -vv --tb=long
   ```

5. **Check code review for context**
   ```bash
   grep -B 5 -A 5 "Issue" CODE_REVIEW.md
   ```
