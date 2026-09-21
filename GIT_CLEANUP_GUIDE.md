# Git Guide: Safely Removing Accidentally Pushed Files & Managing Secrets

Accidentally committing and pushing sensitive files (like `.env`, credentials, private keys) or large unwanted binaries is a common mistake. This guide provides clear, step-by-step workflows to resolve the issue safely and prevent it from recurring.

---

## ⚠️ Golden Rule for Pushed Secrets
> **If you pushed an API key, database password, or token to GitHub, assume it is compromised immediately.**
>
> 1. **Rotate/invalidate the secret immediately** in the third-party dashboard or database.
> 2. Then, follow the steps below to clean your repository.

---

## Method 1: The Quick & Safe Untrack (Recommended for Most Cases)

Use this method when you want to **remove the file from GitHub and future commits**, but **keep the file on your local computer**.

### Step 1: Untrack the file from Git cache
Do **not** use regular `git rm`, as that deletes the file from your local hard drive. Instead, run:

```bash
# For a single file:
git rm --cached path/to/your/file

# Example for .env:
git rm --cached fastapi_basics/.env

# For an entire folder:
git rm -r --cached path/to/folder/
```

### Step 2: Add the file to `.gitignore`
Open your `.gitignore` file (or create one at your project root) and add the file pattern:

```gitignore
# Environment files
.env
*.env
.env.*
.env.local
!.env.example
```

### Step 3: Verify the changes
Run `git status` to verify:

```bash
git status
```

You should see:
- `deleted: path/to/file` under **Changes to be committed** (meaning Git stops tracking it).
- The file is **still present on your machine**.
- Your updated `.gitignore` is ready to stage.

### Step 4: Stage `.gitignore`, commit, and push

```bash
git add .gitignore
git commit -m "chore: stop tracking sensitive file and add to .gitignore"
git push origin <your-branch-name>
```

> **Result**: On GitHub, the file will be removed from your latest codebase. On your local machine, the file remains untouched.

---

## Method 2: Completely Purging from Entire Git History

If you committed a critical password or secret and want to ensure it cannot be found by someone browsing past commits, Method 1 is not enough—past commits in Git history still contain the file.

### Step 1: Invalidate / Rotate your secrets first
Never rely solely on history rewriting to secure a leaked secret. Search engines and bots scan public GitHub commits within seconds.

### Step 2: Clean the history using `git-filter-repo` (Recommended tool)
`git-filter-repo` is the modern and official tool recommended by the Git project.

1. **Install `git-filter-repo`** (requires Python):
   ```bash
   pip install git-filter-repo
   ```

2. **Make a backup of your project folder first** in case you need to revert.

3. **Run `git-filter-repo` to purge the file**:
   ```bash
   git filter-repo --invert-paths --path path/to/file
   ```
   *(e.g., `git filter-repo --invert-paths --path fastapi_basics/.env`)*

4. **Re-add your GitHub remote** (`git-filter-repo` removes remotes as a safety precaution to prevent accidental force pushes):
   ```bash
   git remote add origin https://github.com/<username>/<repo>.git
   ```

5. **Force push the rewritten history to GitHub**:
   ```bash
   git push origin --force --all
   ```

> 💡 **Notice for Collaborators**: Anyone else working on this repository will need to re-clone or rebase, because commit hashes will have changed.

---

## Best Practices: How to Prevent Leaks in the Future

### 1. Maintain a `.env.example` Template
Never commit real secrets, but **do** commit a template file so teammates and deployment environments know what variables are expected.

Create `.env.example`:
```env
# Database Settings
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# API Keys
SECRET_KEY=your-secret-key-here
DEBUG=True
```

Add documentation instructing developers to copy it:
```bash
cp .env.example .env
```

### 2. Have a Solid Root `.gitignore`
Place a comprehensive `.gitignore` at the very root of your repository before starting development:

```gitignore
# Secrets & Environment variables
.env
*.env
.env.*
.env.local
!.env.example


# Python artifacts
__pycache__/
*.py[cod]
*.pyc

# Virtual environments
.venv/
env/
venv/

# Editor configurations
.vscode/
.idea/
```

### 3. Enable GitHub Secret Scanning & Push Protection
If your repository is on GitHub:
1. Go to repository **Settings** > **Code security and analysis**.
2. Enable **Secret scanning** and **Push protection**.
3. GitHub will block commits that contain detected tokens before they can even be pushed.

### 4. Use Pre-commit Secret Scanners
Catch mistakes locally before typing `git commit`:
- [Gitleaks](https://github.com/gitleaks/gitleaks): Scans staged changes for passwords and tokens.
- [pre-commit](https://pre-commit.com): Easily sets up pre-commit hooks to block `.env` files and large files automatically.

---

## Quick Command Reference

| Action | Command |
| :--- | :--- |
| **Stop tracking a file without deleting it locally** | `git rm --cached <file>` |
| **Stop tracking an entire folder without deleting** | `git rm -r --cached <dir>` |
| **Check which files Git is tracking** | `git ls-files` |
| **Check if a specific file is tracked** | `git ls-files <file>` |
| **Check which `.gitignore` rule is ignoring a file** | `git check-ignore -v <file>` |
| **Push your commit to GitHub** | `git push origin <branch>` |
| **Force push after rewriting history** | `git push origin --force-with-lease` |
