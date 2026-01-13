Great question! Let me explain the purpose of each and why they work together:

## pytest.ini

**Purpose**: Project-wide pytest configuration file

Think of `pytest.ini` as the **"settings file"** for your entire test suite. It tells pytest how to behave across all test runs.

**What it does:**
- **Test Discovery**: Tells pytest which files/functions are tests (`test_*.py`, `Test*` classes)
- **Default Options**: Adds command-line flags automatically (like `-v` for verbose)
- **Marker Registration**: Defines custom markers (`@pytest.mark.integration`)
- **Output Formatting**: Controls how test results appear in terminal
- **Global Settings**: Things that apply to every test run

**Example from your file:**
```ini
testpaths = tests  # Only look in 'tests' folder
addopts = -v --strict-markers  # Always run verbose, enforce marker registration
```

**When pytest looks for it**: At project root, automatically loaded on every `pytest` command.

---

## conftest.py

**Purpose**: Shared test code and fixtures

Think of `conftest.py` as the **"shared library"** for your tests. It provides reusable components that multiple test files can access.

**What it does:**
- **Fixtures**: Shared test data/setup (like `@pytest.fixture def sample_data()`)
- **Hooks**: Custom behavior during test execution (like skipping integration tests)
- **Path Setup**: Add directories to Python's import path
- **Dynamic Configuration**: Programmatic control over test collection/execution

**Example from your file:**
```python
def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration flag is used"""
    # This runs BEFORE tests execute
    if not config.getoption("--run-integration"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
```

**Special feature**: Any `conftest.py` is automatically discovered and loaded. You can have multiple:
- `tests/conftest.py` (available to all tests)
- `tests/integration/conftest.py` (available only to integration tests)

---

## How They Work Together

```
pytest.ini (declares)          conftest.py (implements)
├─ "markers: integration"  →   pytest_configure() registers it
├─ "testpaths = tests"     →   sys.path modification finds modules
└─ Custom CLI options      →   pytest_addoption() defines them
                               pytest_collection_modifyitems() uses them
```

### Example Flow:

1. **You run**: `pytest`
2. **pytest.ini says**: "Look in `tests/` folder, run verbose, use strict markers"
3. **conftest.py loads**: Adds `src/` to import path, registers markers
4. **Tests discover**: `conftest.py` checks if `--run-integration` flag exists
5. **Tests run**: Integration tests skipped unless flag present

---

## Real-World Analogy

| File | Analogy | Contains |
|------|---------|----------|
| **pytest.ini** | Restaurant menu | What's available, prices, categories |
| **conftest.py** | Restaurant kitchen | How dishes are prepared, shared ingredients |

---

## Do You Need Both?

**No, but they serve different purposes:**

- **pytest.ini**: Better for **declarative configuration** (settings, options)
- **conftest.py**: Better for **programmatic logic** (fixtures, hooks, custom behavior)

**You could put everything in conftest.py**, but pytest.ini is:
- More readable for configuration
- Easier for non-Python users to modify
- Standard convention in Python projects

---

## Key Differences Summary

| Feature | pytest.ini | conftest.py |
|---------|-----------|-------------|
| **Type** | INI config file | Python code |
| **Purpose** | Settings & options | Shared fixtures & hooks |
| **Syntax** | Key=value pairs | Python functions |
| **Loaded** | Once at startup | Per directory |
| **Best for** | Static configuration | Dynamic behavior |
| **Examples** | Test paths, output format | Fixtures, custom markers, path setup |

---

## Your Specific Use Case

In your test suite:

**pytest.ini**:
```ini
markers = integration: Tests that use real API
```
Declares that `@pytest.mark.integration` is valid.

**conftest.py**:
```python
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        # Skip integration tests
```
Implements the logic to actually skip those tests.

**Result**: 
- Run `pytest` → integration tests skipped ✓
- Run `pytest --run-integration` → all tests run ✓

