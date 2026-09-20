# UV — Python Setup on Windows

This guide explains how to install **UV** on Windows, install Python using UV, create a Python project, and manage a virtual environment.

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

## 6. Create a Virtual Environment

Create a virtual environment using Python 3.12:

```powershell
uv venv --python 3.12
```

This creates a `.venv` directory inside your project.

Your project will look something like:

```text
my-project/
├── .venv/
├── main.py
├── pyproject.toml
└── README.md
```

---

## 7. Activate the Virtual Environment

In PowerShell:

```powershell
.venv\Scripts\activate
```

After activation, your terminal should show the virtual environment name, for example:

```text
(.venv) PS C:\Projects\my-project>
```

You are now working inside the virtual environment.

---

## 8. PowerShell Execution Policy Error

If you get an error such as:

```text
cannot be loaded because running scripts is disabled on this system
```

PowerShell's execution policy is blocking the virtual environment activation script.

You can allow scripts **only for the current PowerShell session** by running:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Then activate the environment again:

```powershell
.venv\Scripts\activate
```

> **Note:** Using `-Scope Process` means the change only applies to the current PowerShell window. Closing the terminal will remove the change.

---

## 9. Deactivate the Virtual Environment

When you are finished working in the virtual environment:

```powershell
deactivate
```

---

## Quick Reference

| Task                       | Command                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------- |
| Install UV                 | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| Check UV                   | `uv --version`                                                                        |
| Install Python             | `uv python install 3.12`                                                              |
| List Python versions       | `uv python list`                                                                      |
| Initialize project         | `uv init projectName`                                                                 |
| Create virtual environment | `uv venv --python 3.12`                                                               |
| Activate environment       | `.venv\Scripts\activate`                                                              |
| Fix PowerShell policy      | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`                    |
| Deactivate environment     | `deactivate`                                                                          |
