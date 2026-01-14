# 1. What uv *is* and what it sets up

uv is:

* a fast Python package installer
* a Python environment manager
* a project manager that understands $pyproject.toml$
* a runtime (`uv run`) that automatically uses the correct environment

uv **does not** create heavy virtual environments like `python -m venv`.
Instead, uv maintains **lightweight environments** stored in:

```
.project_root/.venv/
```

unless configured otherwise.

When you run uv in a project folder with a $pyproject.toml$, it:

1. Detects the project
2. Creates `.venv/` automatically (PEP 582–style layout)
3. Installs the dependencies defined in $pyproject.toml$
4. Keeps everything isolated from global Python installs

You do *not* need to activate the environment manually.
`uv run python` simply uses it.

---

# 2. Using uv with an existing $pyproject.toml$

Assume your directory looks like:

```
my_project/
    pyproject.toml
    src/
        my_project/
            __init__.py
```

### Step 1 — Sync environment with the pyproject

```
uv sync
```

This:

* reads $pyproject.toml$
* resolves dependencies
* installs everything into `.venv/`
* creates `.python-version` for version pinning (if needed)

This is the uv equivalent of:

```
pip install -r requirements.txt
pip install -e .
```

but fully modern.

---

# 3. Add dependencies

To add packages:

```
uv add pandas scikit-learn
```

This modifies $pyproject.toml$ automatically and installs them.

The pyproject becomes the *single source of truth*.

---

# 4. Run anything using uv’s environment

Instead of activating `.venv`, you do:

```
uv run python
```

Or run scripts:

```
uv run src/my_project/train_model.py
```

Or run a module:

```
uv run -m my_project
```

uv ensures you always run inside the managed environment.

---

# 5. Install your own project in editable mode

You can explicitly ensure your package is installed:

```
uv pip install -e .
```

uv uses its own super-fast pip implementation.

---

# 6. Build the project

```
uv build
```

Creates:

* `dist/*.whl`
* `dist/*.tar.gz`

using the build backend from $pyproject.toml$.

---

# 7. Minimal pyproject example (ML-friendly)

Here’s a clean and simple template:

```
[project]
name = "my_project"
version = "0.1.0"
description = "Example project"
requires-python = ">=3.10"
dependencies = [
    "pandas",
    "scikit-learn",
]

[project.optional-dependencies]
dev = [
    "ipykernel",
    "pytest",
]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

uv will fully manage this.

---

# 8. Typical uv workflow (summary)

Inside your project folder:

```
uv sync             # Install everything in pyproject.toml
uv add numpy        # Modify pyproject and install
uv run python       # Run Python with correct environment
uv run my_script.py # Run script or module
uv pip install -e . # Install your package
uv build            # Build distributable packages
```

No manual virtual environments.
No pip freeze.
No requirements.txt.
Everything is driven by the pyproject.


uv sync
uv run python

uv sync                # install deps from pyproject.toml
uv run python script.py
uv add requests        # add a new dependency
uv build               # generate distributable artifacts
uv publish             # (optional) publish to PyPI

# Why use uv & pyproject.toml

A modern Python project typically avoids plain requirements.txt in favour of environment-aware, lockfile-based dependency management. The common, recommended alternatives are:

1. pyproject.toml + a dependency manager (Poetry, PDM, Hatch)

This is now the most modern and widely accepted standard.

How it works:

Dependencies are declared in pyproject.toml under [project] or tool-specific sections.

A lockfile (e.g., poetry.lock, pdm.lock) ensures deterministic builds.

The tool manages environments, installation, version resolution, and publishing.