# Code Improvement Workflow with Tests

This document shows how to use the test suite when making the improvements recommended in CODE_REVIEW.md.

## Workflow Overview

```
1. Identify Issue (in CODE_REVIEW.md)
   ↓
2. Run Relevant Tests (baseline)
   ↓
3. Make Code Changes
   ↓
4. Run Tests Again (verify fix)
   ↓
5. Check for Regressions
```

## Example: Fix Issue #1 - Type Incompatibility

### Issue
Type incompatibility in `apply_chunk_theme()` (prompt.py:340-342)

### Before: Run the Test
```bash
.venv/bin/pytest tests/test_chunks.py::TestChunkApplyTheme -v
```

Output:
```
tests/test_chunks.py::TestChunkApplyTheme::test_apply_theme_path_segment PASSED
tests/test_chunks.py::TestChunkApplyTheme::test_apply_theme_user_segment PASSED
tests/test_chunks.py::TestChunkApplyTheme::test_apply_theme_dollar_segment_no_styling PASSED
tests/test_chunks.py::TestChunkApplyTheme::test_apply_theme_multiple_chunks PASSED
tests/test_chunks.py::TestChunkApplyTheme::test_apply_theme_sink_no_project PASSED
```

Also run mypy to see the current errors:
```bash
.venv/bin/mypy src/
```

Output shows:
```
src/prompt/prompt.py:340: error: Incompatible types in assignment
src/prompt/prompt.py:342: error: Incompatible types in assignment
```

### Make the Fix

Edit `src/prompt/prompt.py` line 340-342:
```python
# OLD CODE - causes type errors
if project_fg.startswith("#"):
    project_fg = hex_to_rgb(project_fg)  # Now a tuple, but typed as str
if project_bg.startswith("#"):
    project_bg = hex_to_rgb(project_bg)  # Now a tuple, but typed as str

# NEW CODE - proper type handling
project_fg_value: str | tuple[int, int, int] = project_fg
project_bg_value: str | tuple[int, int, int] = project_bg

if isinstance(project_fg_value, str) and project_fg_value.startswith("#"):
    project_fg_value = hex_to_rgb(project_fg_value)
if isinstance(project_bg_value, str) and project_bg_value.startswith("#"):
    project_bg_value = hex_to_rgb(project_bg_value)

# Use the properly typed values
rendered_chunks = self._style_chunk(
    project_name,
    fg=project_fg_value,
    bg=project_bg_value,
    # ... rest of args
)
```

### After: Run Tests Again

```bash
.venv/bin/pytest tests/test_chunks.py::TestChunkApplyTheme -v
```

Should still pass!

```bash
.venv/bin/mypy src/
```

Should show no errors on lines 340-342!

### Verify No Regressions

```bash
.venv/bin/pytest tests/ -v
```

Output:
```
93 PASSED  (or 89 PASSED + 4 EXPECTED FAILURES)
```

## Example: Fix Issue #2 - Unused Variables

### Issue
Unused variables in `_chunk_ddev()` (prompt.py:634, 642)

### Before: Run Tests
```bash
.venv/bin/ruff check src/ 2>&1 | grep -A 2 "F841"
```

Output:
```
src/prompt/prompt.py:634:12: F841 Local variable `ddev_dir` is assigned to but never used
src/prompt/prompt.py:642:13: F841 Local variable `clean` is assigned to but never used
```

### Make the Fix

Edit `src/prompt/prompt.py` lines 632-646:

```python
# OLD CODE
def _chunk_ddev(self) -> str:
    ddev = ""
    if ddev_dir := find_dir_upwards(Path(os.path.curdir), ".ddev", stop_at="~"):
        output = subprocess.run(...)
        info = json.loads(output.stdout)["raw"]
        clean = True  # UNUSED!
        color = "green" if info["status"] == "running" else "red"
        extra = (Ellipses.upper_left_square, {"fg": color})
        ddev = self.apply_chunk_theme(Segment.DDEV, ("DDev",), extra=extra)
    return ddev

# NEW CODE
def _chunk_ddev(self) -> str:
    ddev = ""
    if find_dir_upwards(Path(os.path.curdir), ".ddev", stop_at="~"):
        output = subprocess.run(...)
        info = json.loads(output.stdout)["raw"]
        color = "green" if info["status"] == "running" else "red"
        extra = (Ellipses.upper_left_square, {"fg": color})
        ddev = self.apply_chunk_theme(Segment.DDEV, ("DDev",), extra=extra)
    return ddev
```

### After: Run Tests Again

```bash
.venv/bin/ruff check src/
```

Output:
```
No errors found!
```

### Run Tests to Verify

```bash
.venv/bin/pytest tests/test_chunks.py -v
```

Should still pass!

## Example: Fix Issue #3 - Path Prefix Vulnerability

### Issue
String prefix matching in `get_project_dir()` (projects.py:55)

### Before: Run Tests
```bash
.venv/bin/pytest tests/test_projects.py::TestGetProjectDir::test_path_prefix_issue -v
```

Output:
```
PASSED (but this is expected behavior - the bug still exists!)
```

This test demonstrates the bug exists:
```python
@pytest.mark.edge_case
def test_path_prefix_issue(self):
    """Test the path prefix matching vulnerability.

    This tests that /home/myproject2 doesn't match /home/myproject.
    This is currently a bug - it uses string.startswith() instead of
    proper path comparison.
    """
    projects = {"myproject": ["/home/myproject", "#FF0000"]}
    with patch("os.path.realpath", return_value="/home/myproject2/src"):
        result = get_project_dir(projects)
        # Currently returns the path (bug), should return False
        assert result == "/home/myproject"  # Current buggy behavior
```

### Make the Fix

Edit `src/prompt/projects.py` lines 47-59:

```python
# OLD CODE
def get_project_dir(projects: dict[str, list[str]]) -> str | bool:
    pwd = os.path.realpath(os.path.curdir)
    for project, project_info in projects.items():
        path = project_info[0]
        if pwd == path:
            return False
        if pwd.startswith(path):  # BUG: String prefix matching!
            return path
    return False

# NEW CODE
def get_project_dir(projects: dict[str, list[str]]) -> str | bool:
    pwd = Path(os.path.realpath(os.path.curdir))
    for project, project_info in projects.items():
        path = Path(project_info[0])
        if pwd == path:
            return False
        try:
            if pwd.is_relative_to(path):  # FIXED: Proper path comparison
                return str(path)
        except ValueError:
            # is_relative_to raises ValueError if not relative
            continue
    return False
```

### After: Update Test

Now update the test to expect the correct behavior:

```python
@pytest.mark.edge_case
def test_path_prefix_issue(self):
    """Test the path prefix matching is fixed with proper path comparison."""
    projects = {"myproject": ["/home/myproject", "#FF0000"]}
    with patch("os.path.realpath", return_value="/home/myproject2/src"):
        result = get_project_dir(projects)
        # Should return False, not match due to string prefix
        assert result is False
```

### Run Tests

```bash
.venv/bin/pytest tests/test_projects.py::TestGetProjectDir -v
```

Should show:
```
test_in_project_root PASSED
test_in_project_subdirectory PASSED
test_not_in_any_project PASSED
test_path_prefix_issue PASSED  ← Now passes with fix!
test_multiple_projects_selects_closest PASSED  ← Now also passes!
```

## Example: Fix Issue #4 - Unsafe `stty` Parsing

### Issue
No error handling for `stty size` command failure (prompt.py:252)

### Before: Run Tests
```bash
.venv/bin/pytest tests/test_chunks.py::TestChunksInit::test_chunks_init_invalid_stty -v
```

Output:
```
PASSED (expects ValueError to be raised)
```

### Make the Fix

Edit `src/prompt/prompt.py` lines 248-260:

```python
# OLD CODE
def __init__(self) -> None:
    ssh_location = "Remote" if self.IS_SSH else "Local"
    self.theme = self._get_theme(ssh_location)
    self.segment_lengths: list[int] = []
    _, self.columns = os.popen("stty size", "r").read().split()  # No error handling!
    # ...

# NEW CODE (using shutil which is more robust)
import shutil

def __init__(self) -> None:
    ssh_location = "Remote" if self.IS_SSH else "Local"
    self.theme = self._get_theme(ssh_location)
    self.segment_lengths: list[int] = []

    # Use shutil.get_terminal_size() instead of stty
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    self.columns = str(terminal_size.columns)
    # ...
```

### After: Run Tests

```bash
.venv/bin/pytest tests/test_chunks.py::TestChunksInit -v
```

Should still pass!

```bash
.venv/bin/pytest tests/test_chunks.py -v
```

All Chunks tests should pass!

## Running Full Test Suite After Changes

After each improvement, always run the full suite:

```bash
# Run all tests
.venv/bin/pytest tests/ -v

# Run with coverage to see if you improved code quality
.venv/bin/pytest tests/ --cov=src/prompt --cov-report=term-missing

# Run type checker
.venv/bin/mypy src/

# Run linter
.venv/bin/ruff check src/
```

## Checklist for Each Improvement

- [ ] Identified the issue in CODE_REVIEW.md
- [ ] Found related tests in test suite
- [ ] Ran tests before making changes
- [ ] Made the code change
- [ ] Ran tests after changes
- [ ] All tests pass (or expected failures are unchanged)
- [ ] No new regressions
- [ ] Linter passes (ruff check)
- [ ] Type checker passes (mypy)
- [ ] Coverage didn't decrease

## Expected Outcomes

After all improvements are complete, you should see:

1. **All utility function tests passing** - colorscale, hex_to_rgb, path matching, etc.
2. **All project management tests passing** - CSV I/O, project detection, filtering
3. **All Chunks tests passing** - Prompt generation, theme application
4. **All CLI tests passing** - Command execution, project management
5. **Mypy clean** - No type errors
6. **Ruff clean** - No linting errors
7. **100% passing tests** - All 93 tests pass (currently 89 + 4 expected failures that will be fixed)

## Example: Multi-Issue Fix Session

Fix multiple issues in one session:

```bash
# Start
.venv/bin/pytest tests/ -v --tb=short  # 89 passed, 4 failed

# Fix Issue #1 (type error)
# ... edit code ...
.venv/bin/pytest tests/test_chunks.py -v  # Still passing

# Fix Issue #2 (unused variables)
# ... edit code ...
.venv/bin/ruff check src/  # No errors

# Fix Issue #3 (path prefix)
# ... edit code and test ...
.venv/bin/pytest tests/test_projects.py::TestGetProjectDir -v  # Now 5/5 pass!

# Fix Issue #4 (stty parsing)
# ... edit code ...
.venv/bin/pytest tests/test_chunks.py::TestChunksInit -v  # Still passing

# Final check
.venv/bin/pytest tests/ -v  # 93 passed! 🎉
```

## Questions About a Failing Test?

If a test fails unexpectedly:

1. Run the test in isolation with full output:
   ```bash
   .venv/bin/pytest tests/test_file.py::TestClass::test_method -vv --tb=long
   ```

2. Check what the test is actually testing:
   ```bash
   grep -A 20 "def test_method" tests/test_file.py
   ```

3. Verify your change didn't affect something unexpected:
   ```bash
   git diff src/  # See what you changed
   ```

4. If the test is wrong (not the code), update the test:
   ```bash
   # Edit the test to match the new behavior
   nano tests/test_file.py
   .venv/bin/pytest tests/test_file.py::TestClass::test_method -v
   ```
