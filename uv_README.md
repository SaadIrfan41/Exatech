# UV — Python Setup on Windows

This guide explains how to install **UV** on Windows, install Python using UV, create a Python project, and run your project with automatic virtual environment management.

## 1. Install UV

Open **PowerShell** and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. Check if UV is Installed

Verify the installation:

```powershell
uv --version
```

If UV is installed correctly, this will display the installed UV version.

---

## 3. Install Python Using UV

Install Python 3.12:

```powershell
uv python install 3.12
```

UV will download and install Python for you.

---

## 4. Check Installed Python Versions

To see all Python versions installed and available through UV:

```powershell
uv python list
```

---

## 5. Initialize a New Project

Create a new Python project:

```powershell
uv init projectName --no-package
```

For example:

```powershell
uv init my-project --no-package
```

Then move into the project directory:

```powershell
cd my-project
```

---

## 6. Run Your Project (Automatic Virtual Environment)

With UV, you **do not need to manually create or activate a virtual environment**. UV automatically creates and manages the `.venv` directory for you whenever you run commands or add dependencies.

Run your script:

```powershell
uv run main.py
```

Add dependencies (UV automatically creates/updates `.venv` and installs packages):

```powershell
uv add <package-name>
```

Your project directory will look something like:

```text
my-project/
├── .venv/            # Managed automatically by UV
├── main.py
├── pyproject.toml
└── uv.lock
```

---

## Quick Reference

| Task                 | Command                                                                               |
| -------------------- | ------------------------------------------------------------------------------------- |
| Install UV           | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| Check UV             | `uv --version`                                                                        |
| Install Python       | `uv python install 3.12`                                                              |
| List Python versions | `uv python list`                                                                      |
| Initialize project   | `uv init projectName --no-package`                                                    |
| Run script           | `uv run main.py`                                                                      |
| Add package          | `uv add <package>`                                                                    |
