# Working With Shell: Part 1

A step-by-step introduction to the Linux command line for beginners and aspiring system administrators.

By the end of this guide you will be able to move around the filesystem, create and manage files and directories, find help when you are stuck, and customize your Bash shell.

---

## Table of Contents

1. [What is the Shell?](#1-what-is-the-shell)
2. [Anatomy of a Command](#2-anatomy-of-a-command)
3. [Internal vs. External Commands](#3-internal-vs-external-commands)
4. [Navigating the Filesystem](#4-navigating-the-filesystem)
5. [Creating, Copying, Moving and Deleting](#5-creating-copying-moving-and-deleting)
6. [Viewing and Creating File Contents](#6-viewing-and-creating-file-contents)
7. [Listing Files with `ls`](#7-listing-files-with-ls)
8. [Getting Help](#8-getting-help)
9. [The Bash Shell and Its Productivity Features](#9-the-bash-shell-and-its-productivity-features)
10. [Environment Variables and `$PATH`](#10-environment-variables-and-path)
11. [Customizing Your Prompt (`$PS1`)](#11-customizing-your-prompt-ps1)
12. [Final Practice Lab](#12-final-practice-lab)
13. [Cheat Sheet](#13-cheat-sheet)

---

## 1. What is the Shell?

The **shell** is a program that lets you talk to the operating system by typing text commands. You type a command, the shell interprets it, passes it to the Linux kernel, and prints the result.

A graphical interface (GUI) is friendly, but it only exposes the actions its designers built buttons for. The shell gives you far more power and flexibility, and it is the main tool of every Linux system administrator. It also works over a remote connection where no GUI exists.

### Your home directory

When you log in, you start in your **home directory**. Each regular user gets one, usually at `/home/<username>`:

- User `alice` has `/home/alice`
- User `bob` has `/home/bob`

Think of it as your personal locker. You have full access to it, and other regular users cannot read your files there.

In the prompt and in commands, the tilde `~` is shorthand for your home directory. So `~` and `/home/alice` mean the same thing for alice.

### Try it

```bash
pwd          # print where you are right now
echo $HOME   # print the path of your home directory
```

---

## 2. Anatomy of a Command

Every command has up to three parts:

```
command  [options]  [arguments]
  ls       -l         /etc
```

| Part | What it does | Example |
| :--- | :--- | :--- |
| **Command** | The program to run | `echo` |
| **Options** (flags, switches) | Change *how* it behaves. Start with `-` (short, usually one letter) or `--` (long name) | `-n`, `--help` |
| **Arguments** | What the command works on: text, files, directories | `Hello`, `/etc` |

Some commands need arguments, others do not.

```bash
echo                  # no argument: prints an empty line
echo Hello World      # argument: prints "Hello World"
echo -n Hello World   # option -n: prints without the trailing newline
uptime                # needs no arguments: shows how long the system has been running
```

> **Tip:** You will never remember every option of every command. Learn how to look them up instead (see [Getting Help](#8-getting-help)).

---

## 3. Internal vs. External Commands

| Type | What it is | Examples |
| :--- | :--- | :--- |
| **Internal (built-in)** | Part of the shell itself | `cd`, `pwd`, `echo`, `export`, `type` |
| **External** | A separate program or script stored as a file on disk | `mv`, `cp`, `mkdir`, `rm`, `ls` |

Use `type` to find out which kind a command is:

```bash
type cd      # cd is a shell builtin
type mv      # mv is /usr/bin/mv
type -a echo # show every place "echo" is found
```

> **Note:** On many systems `type ls` reports `ls` as an **alias** (for example `ls --color=auto`). Aliases are covered in [section 9](#9-the-bash-shell-and-its-productivity-features).

---

## 4. Navigating the Filesystem

### Absolute vs. relative paths

- **Absolute path**: starts at the root directory `/` and works from anywhere. Example: `/home/alice/Asia/India`
- **Relative path**: starts from where you currently are. Example: `Asia/India`

Two special names are available in every directory:

| Symbol | Meaning |
| :--- | :--- |
| `.` | The current directory |
| `..` | The parent directory (one level up) |

### Moving around

```bash
pwd              # where am I?
cd Asia          # relative path: go into Asia
cd ..            # go up one level
cd /home/alice   # absolute path
cd ~             # go home (same as just: cd)
cd -             # jump back to the previous directory
```

### The directory stack: `pushd` and `popd`

`pushd` changes directory *and* remembers where you were. `popd` takes you back.

```bash
pushd /etc    # go to /etc, remember current location
# ...do some work...
popd          # return to where you started
dirs          # show the current stack
```

You can push several directories; `popd` returns them last-in, first-out.

---

## 5. Creating, Copying, Moving and Deleting

We will use a small continents example throughout this section.

### Create directories: `mkdir`

```bash
mkdir Asia Europe Africa America      # several at once
mkdir Asia/China                       # using a relative path
mkdir Asia/India/Mumbai                # FAILS if Asia/India does not exist
mkdir -p Asia/India/Mumbai             # -p creates missing parents too
```

### Create an empty file: `touch`

```bash
touch Asia/China/country.txt
```

`touch` on an existing file just updates its timestamp.

### Copy: `cp`

```bash
cp Asia/India/Mumbai/city.txt Africa/Egypt/Cairo/   # copy a file
cp -r Asia Asia_backup                              # -r is required for directories
```

### Move and rename: `mv`

`mv` does both jobs. The only difference is the destination.

```bash
mv Europe/Morocco Africa/       # move a directory into Africa
mv Asia/India/Mumbao Asia/India/Mumbai   # rename (fix a typo)
mv -i file1.txt file2.txt       # -i asks before overwriting
```

### Delete: `rm`

```bash
rm London/Tottenham.txt   # delete a file
rm -r old_folder          # -r deletes a directory and everything inside
```

> ⚠️ **There is no recycle bin in the shell.** Deleted files are gone. Double-check before using `rm -r`, and be extra careful with `-f` (force), which skips all confirmation.

---

## 6. Viewing and Creating File Contents

### Display a file: `cat`

```bash
cat city.txt      # print the whole file
cat -n city.txt   # with line numbers
```

### Write to a file with `cat` and `>`

```bash
cat > notes.txt
```

Type your text, press **Enter** for new lines, then press **Ctrl+D** to save and exit.

> ⚠️ `>` **overwrites** the file. Anything that was in it is replaced. (Other ways to redirect output, including appending, come in Part 2.)

### Read long files page by page: `less` and `more`

```bash
less /var/log/syslog
```

| Key | Action |
| :--- | :--- |
| `Space` | Next screen |
| `Enter` | Next line |
| `b` | Back one screen |
| `/pattern` | Search for text |
| `q` | Quit |

`less` is generally preferred over `more`, because `more` is the older and more limited pager, while `less` lets you scroll both ways and handles large files well.

---

## 7. Listing Files with `ls`

```bash
ls          # simple list
ls -l       # long format: permissions, owner, size, modified time
ls -a       # include hidden files (names starting with .)
ls -lh      # long format with human-readable sizes (KB, MB)
ls -lt      # sort by modified time, newest first
ls -ltr     # reverse the sort: oldest first, newest at the bottom
ls -R       # list subdirectories recursively
```

Flags can be combined, so `ls -lah` means long + all + human-readable.

Hidden files are common for configuration (for example `~/.bashrc`). The entries `.` and `..` you see with `ls -a` are the current and parent directories from [section 4](#4-navigating-the-filesystem).

---

## 8. Getting Help

You do not need to memorize everything. These four tools are the ones to reach for:

| Tool | Use it when | Example |
| :--- | :--- | :--- |
| `whatis <cmd>` | You want a one-line description | `whatis tar` |
| `<cmd> --help` | You want a quick syntax and option summary | `mkdir --help` |
| `man <cmd>` | You want the full manual with details and examples | `man ls` |
| `apropos <keyword>` | You do not know the command name | `apropos partition` |

Notes:

- Inside `man`: `Space` scrolls down, `b` scrolls up, `/text` searches, `q` quits.
- `apropos keyword` searches all manual page names and descriptions. It is the same as `man -k keyword`.
- If `whatis` or `apropos` return nothing, the manual database may need building: run `sudo mandb`.
- Shell builtins like `cd` may not have their own man page. Use `help cd` instead.
- Many commands also print their usage if you run them incorrectly.

---

## 9. The Bash Shell and Its Productivity Features

### Shell types

There are several shells: `sh` (Bourne shell, from the 1970s), `csh`, `ksh`, `zsh`, and **`bash`** (the "Bourne-Again Shell"), which is the default on most Linux distributions. They all do the same basic job but differ in features and syntax. This guide uses Bash.

```bash
echo $SHELL            # which shell is my login shell? (note: uppercase)
chsh -s /bin/bash      # change login shell (asks for your password)
```

Log out and back in for `chsh` to take effect.

### Tab completion

Type the first few characters of a command, file or directory and press **Tab**. Bash completes it. If there are several matches, press **Tab twice** to list them. This saves typing and prevents typos.

### Aliases

An alias is a custom shortcut for a command.

```bash
alias dt='date'
alias ll='ls -lah'
dt              # runs: date
alias           # list all aliases
unalias dt      # remove an alias
```

### Command history

```bash
history             # list previously run commands, numbered
history | tail -n 10   # last 10 only
!42                 # re-run command number 42
history -c          # clear the history
```

Pressing the **Up arrow** also cycles through previous commands, and **Ctrl+R** searches them.

> **Important:** Aliases, variables and prompts that you set at the command line last only for that terminal session. To make them permanent, add them to `~/.bashrc`, then reload it with `source ~/.bashrc`.

---

## 10. Environment Variables and `$PATH`

A **variable** stores a piece of information. An **environment variable** stores information about your session that the shell and the programs it starts can use. You read a variable by putting `$` in front of its name.

```bash
echo $HOME      # your home directory
echo $USER      # your username
echo $SHELL     # your login shell
env             # list all environment variables
env | grep USER # filter the list
```

### Setting variables

```bash
export OFFICE="caleston"   # available to the shell AND programs it starts
COLOR=blue                 # available only inside the current shell
```

To keep a variable after logging out, put the `export` line in `~/.bashrc` or `~/.profile`.

### How the shell finds commands: `$PATH`

When you type `ls`, the shell does not search the whole disk. It looks through the directories listed in `$PATH`, separated by colons, in order.

```bash
echo $PATH
which ls         # shows the full path of the executable that will run
which python3
which obs        # prints nothing if it is not in PATH
```

If a program is not in a `$PATH` directory, you get `command not found`. To add a directory:

```bash
export PATH=$PATH:/opt/OBS/bin
which obs        # now it is found
```

`$PATH:/opt/OBS/bin` means "keep the existing path and add this directory at the end." Never write `export PATH=/opt/OBS/bin` alone, because that **replaces** the whole list and basic commands stop working in that session.

---

## 11. Customizing Your Prompt (`$PS1`)

The text you see before your cursor is the **prompt**, and it is stored in the `PS1` variable.

```bash
echo $PS1
```

You can change it instantly:

```bash
export PS1="Ubuntu server: "
export PS1='[\u@\h \w]\$ '
```

Common escape codes:

| Code | Meaning |
| :--- | :--- |
| `\u` | Username |
| `\h` | Hostname |
| `\w` | Full current directory (`\W` = just the last folder name) |
| `\d` | Date |
| `\t` | Time (24-hour) |
| `\$` | `$` for a regular user, `#` for root |

**Why this matters:** showing the username and hostname in your prompt helps you avoid running a command on the wrong server when you are logged into several at once.

---

## 12. Final Practice Lab

Work through these in your own terminal. Use `echo $HOME`, `pwd` and `ls` to check your work along the way.

**Part A: Build a directory tree**

1. Go to your home directory with `cd`.
2. Create the structure in one command:
   `mkdir -p continents/Asia/India/Mumbai continents/Africa/Egypt continents/Europe/UK`
3. Verify it with `ls -R continents`.

**Part B: Work with files**

4. Create an empty file: `touch continents/Asia/India/Mumbai/city.txt`
5. Write text into it: `cat > continents/Asia/India/Mumbai/city.txt` (type a line, press Ctrl+D)
6. Read it back with `cat`.
7. Copy it: `cp continents/Asia/India/Mumbai/city.txt continents/Africa/Egypt/`
8. Rename a folder: `mv continents/Europe/UK continents/Europe/UnitedKingdom`
9. Back up the whole tree: `cp -r continents continents_backup`
10. Delete the backup: `rm -r continents_backup`

**Part C: Navigation**

11. Run `pushd continents/Africa`, check `pwd`, then run `popd`.
12. Use `cd -` to jump between two directories.

**Part D: Get help**

13. Run `whatis cat`, `whatis rm`, `whatis mv`.
14. Open `man ls`, search for `-h` using `/-h`, then press `q`.
15. Run `apropos compress` to discover compression tools.

**Part E: Customize your shell**

16. Run `type echo`, `type cd`, `type mv`, `type ls` and note which are built-in.
17. Create an alias: `alias now='date "+%Y-%m-%d %H:%M:%S"'` and run `now`.
18. Run `echo $PATH` and `which ls`, `which bash`, `which touch`.
19. Change your prompt: `export PS1="[\u@\h \W]\$ "`.
20. Make the alias permanent by adding it to `~/.bashrc`, then run `source ~/.bashrc`.

> **Lab tip:** Linux is **case-sensitive**. `Birds`, `birds` and `Bird` are three different names. If an automated check fails, compare the exact spelling and capitalization of what you created against what was asked.

---

## 13. Cheat Sheet

| Command | Purpose |
| :--- | :--- |
| `pwd` | Print current directory |
| `cd <path>` / `cd` / `cd ..` / `cd -` | Change directory / home / up / previous |
| `pushd` / `popd` / `dirs` | Directory stack |
| `ls -lah` | Detailed listing including hidden files |
| `ls -ltr` | Sort by time, oldest first |
| `mkdir -p a/b/c` | Create nested directories |
| `touch <file>` | Create empty file or update timestamp |
| `cp [-r] src dest` | Copy files or directories |
| `mv src dest` | Move or rename |
| `rm [-r] <target>` | Delete (no undo!) |
| `cat <file>` / `cat > <file>` | Show file / write file (Ctrl+D to save) |
| `less <file>` | Page through a file |
| `echo <text>` | Print text |
| `type <cmd>` | Built-in or external? |
| `whatis` / `man` / `--help` / `apropos` | Get help |
| `echo $SHELL` / `chsh -s` | Check / change shell |
| `alias` / `history` | Shortcuts / command history |
| `env` / `export VAR=value` | List / set environment variables |
| `which <cmd>` | Find a command in `$PATH` |
| `export PS1='...'` | Customize prompt |

---

**Next up:** Part 2 builds on this with redirection, variables in depth, and scripting basics.