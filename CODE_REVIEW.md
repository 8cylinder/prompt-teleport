# Code Review: Prompt Project

## Summary

The codebase is well-structured with clean separation of concerns. It uses modern Python features (3.13+) and follows a reasonable architectural pattern. However, there are several actionable improvements in type safety, error handling, and code cleanliness.

---

## 🔴 Critical Issues

### 1. Type Incompatibility in `apply_chunk_theme` (prompt.py:340-342)

**Issue**: Variables assigned RGB tuples but typed as strings.

```python
# Lines 340-342 (currently)
if project_fg.startswith("#"):
    project_fg = hex_to_rgb(project_fg)  # Returns tuple[int, int, int]
if project_bg.startswith("#"):
    project_bg = hex_to_rgb(project_bg)  # Returns tuple[int, int, int]

# But project_fg and project_bg are declared as str
# in get_project_info() return statement
```

**Impact**: Type checker (mypy) fails. Could cause runtime errors if click.style() receives unexpected types.

**Solution**: Update the function signature and type handling. Define project_fg/bg as `str | tuple[int, int, int]` union type, or convert them earlier in the function flow.

---

### 2. Unused Variables (prompt.py:634, 642)

**Issue**: Linter detected unused variable assignments:
- `ddev_dir` assigned but never used (line 634)
- `clean` assigned but never used (line 642)

```python
# Line 634 - ddev_dir is checked but not used
if ddev_dir := find_dir_upwards(Path(os.path.curdir), ".ddev", stop_at="~"):
    # ddev_dir is never referenced again

# Line 642 - clean is assigned but not used
clean = True
color = "green" if info["status"] == "running" else "red"
# clean variable is unused
```

**Impact**: Code cleanliness; indicates incomplete refactoring or dead code.

**Solution**:
- Remove the unused `clean = True` assignment
- The `ddev_dir` check is just for existence; use `if find_dir_upwards(...):` without walrus operator

---

## 🟡 High Priority Issues

### 3. Unsafe Terminal Width Parsing (prompt.py:252)

**Issue**: No error handling for `stty size` command failure.

```python
_, self.columns = os.popen("stty size", "r").read().split()
```

**Problems**:
- No try/except for unpacking errors
- `stty` may fail or return empty string in non-TTY environments
- Will crash with `ValueError` if unpacking fails
- `self.columns` will be a string, then converted to int later (line 282) without validation

**Solution**:
```python
try:
    _, self.columns = os.popen("stty size", "r").read().split()
except (ValueError, IndexError):
    # Fall back to default or use shutil.get_terminal_size()
    self.columns = "80"  # Default terminal width
```

**Better**: Use `shutil.get_terminal_size()` instead, which is more robust.

---

### 4. Path Traversal Vulnerability in get_project_dir() (projects.py:55)

**Issue**: Simple string prefix matching could cause unexpected behavior.

```python
if pwd.startswith(path):  # Line 55
    return path
```

**Problems**:
- `/home/myproject` would match `/home/myproject2` as a prefix match
- Should verify path is actually a parent directory, not just a string prefix
- Use `Path.is_relative_to()` (which is already used in prompt.py:468!)

**Solution**:
```python
if Path(pwd).is_relative_to(path):
    return path
```

This is the same technique already used in `get_project_info()` at line 468.

---

### 5. IndexError Risk in Git Branch Parsing (prompt.py:573)

**Issue**: Assumes git output format without validation.

```python
lines = stdout.splitlines()
branch = lines[0][3:].split("...")[0]  # Potential IndexError
```

**Problems**:
- If git status returns fewer lines than expected, `lines[0]` will fail
- If the branch line doesn't have "..." separator, slicing could produce unexpected results
- No validation of git output format

**Solution**:
```python
lines = stdout.splitlines()
if not lines or not lines[0].startswith("##"):
    return ""
branch = lines[0][3:].split("...")[0]
```

---

### 6. Stale Documentation in projects.py

**Issue**: Docstring references non-existent file name (projects.py:453, 194)

```python
# Line 453: "Get the project name and color from ~/.sink-projects"
# But actual file is ~/.prompt-projects

# Line 194: References "$HOME/.sink-projects" instead of "$HOME/.prompt-projects"
```

**Solution**: Update comments to reference correct filename.

---

## 🟢 Medium Priority Issues

### 7. Missing Error Handling in subprocess calls

Several subprocess calls lack comprehensive error handling:

**prompt.py:635-640** (ddev):
```python
output = subprocess.run(
    ["ddev", "describe", "--json-output"],
    universal_newlines=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)
info = json.loads(output.stdout)["raw"]  # No error handling!
```

**Problems**:
- If ddev is not installed, this will crash
- If `output.stdout` is empty, `json.loads()` will fail
- No check for subprocess return code
- Missing handling for missing "raw" key

**Solution**:
```python
try:
    output = subprocess.run(
        ["ddev", "describe", "--json-output"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if output.returncode != 0:
        return ""
    info = json.loads(output.stdout).get("raw")
    if not info:
        return ""
    # ... rest of code
except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
    return ""
```

---

### 8. Default Color Scheme Issues (projects.py:111-122)

**Issue**: Random color generation may produce colors with poor contrast.

```python
def get_random_color() -> str:
    hue = round(random.random(), 3)
    value = random.choice([0.15, 0.2, 0.25, 0.3])  # Very dark!
    saturation = random.choice([0.1, 0.2, 0.4, 0.6, 0.8, 1])
    # ...
```

**Problems**:
- `value` (lightness) range [0.15-0.3] is very dark, may be hard to read
- Low saturation with low value can produce indistinguishable colors
- No verification that generated color has sufficient contrast with foreground

**Recommendation**: Document the choices or make them configurable.

---

### 9. Missing newline handling in click output (projects.py:100)

**Issue**: String formatting assumes printf-style output.

```python
out.append(f"{name}  {path}\\n")  # Line 100 - literal \n, not newline
```

**Problems**:
- Uses literal `\\n` instead of actual newline character
- Later passed to `printf` which interprets it, but this is indirect
- Brittle if output method changes

**Solution**:
```python
out.append(f"{name}  {path}\n")  # Use actual newline
print("".join(out), end="")  # Print directly
```

---

## 🔵 Code Quality Observations

### 10. Inconsistent Error Handling Strategy

**Issue**: Mix of different error handling approaches:

- `prompt.py`: Uses custom `error()` function that calls `sys.exit(1)`
- `projects.py`: Uses `error()` that prints printf-style commands
- Different signature: one exits, one doesn't

**Impact**: Confusing for developers; hard to predict behavior.

**Recommendation**: Consolidate error handling or clearly document the differences.

---

### 11. Class-level vs Instance-level Attributes (prompt.py:245-246)

**Issue**: HOME and IS_SSH are class attributes, not instance attributes.

```python
class Chunks:
    HOME: str = os.environ.get("HOME", "")
    IS_SSH: str = os.environ.get("SSH_CLIENT", "")
```

**Problems**:
- Evaluated once at class definition time
- If environment changes (unlikely but possible), instances won't see updates
- Unnecessary; should be instance attributes or functions

**Solution**: Move to `__init__` as instance attributes if per-instance usage is needed.

---

### 12. Dead Code: Virtual Segment (prompt.py:582-586)

**Issue**: `_chunk_virtual()` always returns empty string.

```python
def _chunk_virtual(self) -> str:
    """Requires sudo to work"""
    return ""
    # ... commented-out code below
```

**Problems**:
- Takes up space; the implementation is commented out
- Not actually used (check ps1_prompt() segment list)
- Dead code should be removed or implemented

**Solution**: Either implement properly or remove entirely.

---

### 13. Magic Numbers and Hardcoded Values

**Issue**: Several hardcoded values scattered through code:

- `prompt.py:472`: `colorscale(project_bg, 3)` - Why 3x scale?
- `prompt.py:232`: `sep_position = int(length * position)` - Position magic
- `prompt.py:506`: `max_len = self._get_length(self.snip_char)` - Position 0.25
- `projects.py:113-114`: `value = random.choice([0.15, 0.2, 0.25, 0.3])`

**Recommendation**: Extract to named constants at module level.

---

## ✅ Positive Observations

1. **Good separation of concerns**: UI, prompt logic, and projects are well divided
2. **Type hints**: Consistent use of modern Python type annotations
3. **Click integration**: Proper use of Click library for CLI
4. **Terminal compatibility**: Handles Kitty and iTerm2 correctly
5. **Defensive programming for themes**: Try/except for theme lookups
6. **Path safety**: Uses `Path` objects and `is_relative_to()` where appropriate

---

## Recommended Action Items

### Priority 1 (Fix now):
- [ ] Fix mypy type errors (lines 340-342)
- [ ] Handle `stty size` failure gracefully
- [ ] Fix path prefix matching vulnerability in `get_project_dir()`
- [ ] Add validation to git branch parsing

### Priority 2 (High):
- [ ] Remove unused variable assignments
- [ ] Add error handling to ddev subprocess call
- [ ] Update stale documentation references

### Priority 3 (Nice to have):
- [ ] Consolidate error handling strategy
- [ ] Extract magic numbers to constants
- [ ] Remove or implement dead `_chunk_virtual()`
- [ ] Add comprehensive tests for edge cases

---

## Testing Recommendations

Consider adding tests for:
1. `get_project_dir()` with various path combinations
2. Git branch parsing with different output formats
3. Path snipping with various lengths
4. Color scaling behavior
5. Error cases: missing files, failed commands, invalid terminals
