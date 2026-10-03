"""
extract_linux_guides.py

A Python script that parses WebVTT subtitle files (.vtt) from video courses
and generates clean, beginner-friendly Linux study guides inside step-by-step
subdirectories under `linux_basics/`.

Features:
- Cleans WebVTT cues (strips timestamps, cue IDs, HTML tags, duplicate speech lines).
- Formats transcripts into natural, coherent paragraphs.
- Generates structured, beginner-friendly Markdown study guides (`README.md`) containing:
  * 🎯 Lesson Overview & Objectives
  * 💡 Core Concepts & Analogies (e.g. Bob's learning journey)
  * 💻 Command Reference & Syntax Tables
  * 🛠️ Step-by-Step Hands-On Practice Exercises
  * 📖 Full Cleaned Lecture Transcript
  * 📝 Quick Summary & Review Checklist
- Dynamically discovers all module subfolders inside `linux subtitles/` (starts with
  `working_with_shell`, and automatically handles new modules added in the future).
- Generates a comprehensive Master Index in `linux_basics/README.md`.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional


# Predefined high-quality curricular metadata for known working_with_shell lessons
KNOWN_LESSONS_METADATA = {
    "0125-introduction-to-linux-shell": {
        "title": "Introduction to the Linux Shell",
        "description": "Understand what the shell is, why CLI is preferred over GUI in administration, user home directories, and command syntax basics.",
        "objectives": [
            "Understand the role of the Linux shell as a text-based interface between user and operating system.",
            "Compare GUI vs CLI functionality and system administration power.",
            "Learn user home directory structure (/home/<user> and ~ tilde representation).",
            "Understand basic command syntax: command name, arguments, and options/flags.",
            "Distinguish between internal (built-in) commands and external binary commands."
        ],
        "key_concepts": [
            {
                "term": "What is the Linux Shell?",
                "explanation": "A program that takes typed commands from keyboard, interprets them, and passes them to the Linux operating system kernel to execute. Unlike a Graphical User Interface (GUI), the shell gives complete, unconstrained control over the system."
            },
            {
                "term": "The Home Directory (`/home/<user>` or `~`)",
                "explanation": "Every regular user gets a private workspace called their home directory (e.g., `/home/Michael` or `/home/Bob`). Think of it as a personal locked storage locker. The tilde symbol `~` is shorthand for your personal home directory in the prompt."
            },
            {
                "term": "Command Anatomy (Command + Options + Arguments)",
                "explanation": "A Linux command consists of: (1) **Command name** (what program to run), (2) **Options / Flags** (preceded by `-` or `--`, modifying *how* the program behaves), and (3) **Arguments** (the input or target, such as text, a file, or a directory)."
            },
            {
                "term": "Internal (Built-in) vs. External Commands",
                "explanation": "• **Internal (Built-in)**: Built directly into the shell executable itself (~30 commands, e.g., `cd`, `pwd`, `export`, `type`). Fast execution with zero process overhead.\n• **External**: Standalone executable binaries or scripts located in filesystem directories (e.g., `/usr/bin/mv`, `/bin/ls`). You can check with `type <command>`."
            }
        ],
        "commands": [
            {
                "cmd": "echo <text>",
                "desc": "Print text to the terminal screen.",
                "example": "echo \"Hello, Linux!\"",
                "options": "`-n` suppresses the trailing newline"
            },
            {
                "cmd": "uptime",
                "desc": "Show how long the system has been running since last boot, logged-in users, and load average.",
                "example": "uptime",
                "options": "Runs without arguments"
            },
            {
                "cmd": "type <command>",
                "desc": "Check whether a command is a shell built-in or external binary.",
                "example": "type echo\ntype mv",
                "options": "`-a` shows all locations containing the executable"
            },
            {
                "cmd": "pwd",
                "desc": "Print current working directory.",
                "example": "pwd",
                "options": "Built-in command"
            }
        ],
        "exercises": [
            "Open your terminal and check who you are and where you are: run `pwd` and notice your home directory.",
            "Test `echo` without arguments: run `echo`. Notice it prints an empty line.",
            "Run `echo Hello World` to see argument passing in action.",
            "Run `echo -n Hello World` and observe the difference in newline handling.",
            "Check system uptime using `uptime`.",
            "Determine the type of commands: run `type echo`, `type cd`, `type mv`, `type ls`."
        ]
    },
    "0130-basic-linux-commands": {
        "title": "Basic Linux Commands & Navigation",
        "description": "Master navigation, creating directory hierarchies, absolute vs relative paths, copying, moving, renaming, deleting, and inspecting files.",
        "objectives": [
            "Navigate the filesystem using `pwd`, `cd`, and directory stacks (`pushd` / `popd`).",
            "Differentiate between Absolute Paths (starting from `/`) and Relative Paths (relative to current directory).",
            "Create directories and nested directory trees using `mkdir` and `mkdir -p`.",
            "Manipulate files and folders with `cp`, `mv`, and `rm` (including recursive `-r` flags).",
            "Read and create files with `cat`, redirection `>`, and `touch`.",
            "Inspect files using pagers (`more`, `less`) and explore directory listings with `ls` flags (`-l`, `-a`, `-lt`, `-ltr`)."
        ],
        "key_concepts": [
            {
                "term": "Absolute vs. Relative Paths",
                "explanation": "• **Absolute Path**: Starts from the system root `/` (e.g., `/home/Michael/Asia/India/Mumbai`). It is universally valid regardless of where you are.\n• **Relative Path**: Starts relative to your current location (e.g., `Asia/India` or `../Europe`).\n• `.` (single dot) = Current directory.\n• `..` (double dot) = Parent directory (one level up)."
            },
            {
                "term": "Creating Nested Directories with `-p`",
                "explanation": "`mkdir parent/child/grandchild` fails if parent folders do not exist. Adding the `-p` (parents) flag creates all necessary parent directories along the path in one command."
            },
            {
                "term": "Directory Stack (`pushd` and `popd`)",
                "explanation": "`pushd <dir>` changes to the new folder and pushes your current location onto a stack. When you are done exploring, running `popd` returns you straight back to the saved directory."
            },
            {
                "term": "Listing Hidden Files & Sorting (`ls`)",
                "explanation": "Files starting with `.` are hidden by default in Linux. `ls -a` reveals them. `ls -l` shows detailed permissions/sizes. `ls -lt` sorts by modification time (newest first), and `ls -ltr` reverses it (newest at bottom)."
            }
        ],
        "commands": [
            {
                "cmd": "pwd",
                "desc": "Print Working Directory.",
                "example": "pwd",
                "options": "None required"
            },
            {
                "cmd": "cd <path>",
                "desc": "Change directory. `cd` alone returns to `~` home directory. `cd ..` goes up one level.",
                "example": "cd Asia\ncd ..\ncd ~",
                "options": "`cd -` switches back to previous directory"
            },
            {
                "cmd": "mkdir [-p] <dir>",
                "desc": "Make directory. Use `-p` to create nested parent directories automatically.",
                "example": "mkdir -p Asia/India/Mumbai",
                "options": "`-p` (parents), `-v` (verbose)"
            },
            {
                "cmd": "pushd / popd",
                "desc": "Navigate directories while storing previous locations on a stack.",
                "example": "pushd /etc\n# do work\npopd",
                "options": "`dirs` prints current stack"
            },
            {
                "cmd": "mv <source> <dest>",
                "desc": "Move files/directories or rename them.",
                "example": "mv Europe/Morocco Africa/\nmv Mumbao Mumbai",
                "options": "`-i` prompt before overwrite"
            },
            {
                "cmd": "cp [-r] <source> <dest>",
                "desc": "Copy files. Use `-r` (recursive) when copying folders.",
                "example": "cp Mumbai/city.txt Cairo/\ncp -r Asia Asia_backup",
                "options": "`-r` recursive for directories"
            },
            {
                "cmd": "rm [-r] <target>",
                "desc": "Remove files. Use `-r` to delete non-empty directories.",
                "example": "rm London/Tottenham.txt\nrm -r old_folder",
                "options": "`-r` recursive, `-f` force (use with caution!)"
            },
            {
                "cmd": "touch <filename>",
                "desc": "Create an empty file or update timestamps of an existing file.",
                "example": "touch country.txt",
                "options": "`-a` access time only"
            },
            {
                "cmd": "cat <file>",
                "desc": "Concatenate and display file contents. Also used with `>` to write text.",
                "example": "cat city.txt\ncat > notes.txt\n# type text, press Ctrl+D to save",
                "options": "`-n` number lines"
            },
            {
                "cmd": "more / less <file>",
                "desc": "Paginate large text files. Use Space to advance a page, Enter for a line, `q` to quit.",
                "example": "less /var/log/syslog",
                "options": "Search inside with `/pattern`"
            },
            {
                "cmd": "ls [options] [path]",
                "desc": "List directory contents.",
                "example": "ls -l\nls -a\nls -ltr",
                "options": "`-l` long list, `-a` all (including hidden), `-t` time sorted, `-r` reverse order, `-h` human-readable sizes"
            }
        ],
        "exercises": [
            "In your home directory, build a continent structure: `mkdir -p continents/Asia/India continents/Africa/Egypt continents/Europe/UK`.",
            "Verify the tree using `ls -R continents` or `find continents`.",
            "Create a file `continents/Asia/India/delhi.txt` using `touch continents/Asia/India/delhi.txt`.",
            "Add notes to it using `cat > continents/Asia/India/delhi.txt`, type text, and exit with `Ctrl+D`.",
            "Copy `delhi.txt` to `continents/Africa/Egypt/` using `cp continents/Asia/India/delhi.txt continents/Africa/Egypt/`.",
            "Rename or move a folder: `mv continents/Europe/UK continents/Europe/UnitedKingdom`.",
            "Test directory stack: `pushd continents/Africa` -> check `pwd` -> run `popd` to return home."
        ]
    },
    "0132-command-line-help": {
        "title": "Getting Help in the Linux Command Line",
        "description": "Learn how to discover commands, understand flags, read man pages, and find keywords using whatis and apropos.",
        "objectives": [
            "Quickly get single-line summaries of what a command does using `whatis`.",
            "Explore in-depth documentation, options, and examples using `man` (manual) pages.",
            "Use built-in short help flags (`-h` / `--help`) for fast CLI guidance.",
            "Search for unknown commands by keyword across man descriptions using `apropos`."
        ],
        "key_concepts": [
            {
                "term": "`whatis` — Quick One-Line Summary",
                "explanation": "When you encounter a command name and just need to know its general purpose in one sentence without reading a 50-page manual, run `whatis <command>`."
            },
            {
                "term": "`man` Pages — The Complete Reference Manual",
                "explanation": "Linux comes pre-packaged with offline comprehensive documentation for system calls, CLI commands, and configuration files. Inside `man`: use `Space` (scroll down), `b` (scroll up), `/pattern` (search), and `q` (quit)."
            },
            {
                "term": "Command Help Flags (`-h` and `--help`)",
                "explanation": "Almost every modern CLI program provides a fast synopsis of its syntax and options directly in terminal when passed `--help` or `-h`."
            },
            {
                "term": "`apropos` — Search by Keyword",
                "explanation": "If you don't know the exact command name (for instance, you need to manage network or kernel modules), `apropos keyword` searches every manual page name and summary for that keyword."
            }
        ],
        "commands": [
            {
                "cmd": "whatis <command>",
                "desc": "Display one-line manual page descriptions.",
                "example": "whatis ls\nwhatis mkdir\nwhatis tar",
                "options": "Requires mandb to be initialized (`mandb`)"
            },
            {
                "cmd": "man <command>",
                "desc": "Open the full reference manual for a command or config file.",
                "example": "man ls\nman pushd",
                "options": "`q` to exit, `/keyword` to search"
            },
            {
                "cmd": "<command> --help / -h",
                "desc": "Print built-in command line help synopsis.",
                "example": "mkdir --help\nls --help",
                "options": "Fast in-terminal overview"
            },
            {
                "cmd": "apropos <keyword>",
                "desc": "Search the manual page names and descriptions for a keyword.",
                "example": "apropos copy\napropos partition\napropos modprobe",
                "options": "Equivalent to `man -k`"
            }
        ],
        "exercises": [
            "Run `whatis cat`, `whatis rm`, and `whatis mv` to inspect their quick descriptions.",
            "Open the manual for `ls`: run `man ls`. Practice searching for `-h` by typing `/-h` and pressing Enter. Press `q` to exit.",
            "Run `cp --help` to see the built-in switch descriptions.",
            "Search for compression commands: run `apropos compress` or `apropos backup`."
        ]
    },
    "0135-lab-intro": {
        "title": "Hands-on Lab Environment Introduction",
        "description": "Get familiar with the interactive hands-on lab portal, terminal interface, validation checks, and debugging configuration tasks.",
        "objectives": [
            "Navigate split-screen interactive learning portals (terminal on the left, challenges on the right).",
            "Solve multiple-choice inspection questions by querying the system using commands like `echo $HOME`.",
            "Execute configuration tasks (creating files, directories, permissions) and trigger validation checks.",
            "Troubleshoot task validation failures using error details and hint utilities."
        ],
        "key_concepts": [
            {
                "term": "Dual-Pane Hands-on Lab Workflow",
                "explanation": "Hands-on labs pair a live Linux shell on one side with challenge tasks on the other. Instead of passive watching, students verify concepts by performing active configurations."
            },
            {
                "term": "System Inspection for Quiz Answers",
                "explanation": "When asked multiple-choice questions about the lab environment (e.g., 'What is Bob's home directory?'), never guess — query the system directly using inspection commands (e.g., `echo $HOME` or `pwd`)."
            },
            {
                "term": "Exact Match & Typo Sensitivity in Linux",
                "explanation": "Linux is strictly case-sensitive. Creating `Birds` vs `Bird` or `file.txt` vs `File.txt` causes automated checks to fail. Always double-check exact casing and spelling."
            },
            {
                "term": "Debugging Validation Failures",
                "explanation": "If a check fails: (1) Click error details / inspection log to see what was expected vs found, (2) Re-read requirements carefully, (3) Use the Hint button if stuck."
            }
        ],
        "commands": [
            {
                "cmd": "echo $HOME",
                "desc": "Print the current user's configured home directory path.",
                "example": "echo $HOME",
                "options": "Prints `/home/<username>`"
            },
            {
                "cmd": "mkdir /home/Bob/birds",
                "desc": "Create the required challenge directory inside the home folder.",
                "example": "mkdir -p ~/birds",
                "options": "Double check spelling and capitalization"
            }
        ],
        "exercises": [
            "Check your current environment variables: run `echo $HOME` and `echo $USER`.",
            "Create a test lab practice directory: `mkdir -p ~/lab_practice/birds`.",
            "Verify the directory exists and check its permissions: `ls -ld ~/lab_practice/birds`.",
            "Practice fixing a typo: rename `birds` to `Birds_Backup` using `mv ~/lab_practice/birds ~/lab_practice/Birds_Backup`."
        ]
    },
    "0150-bash-shell": {
        "title": "Bash Shell Deep Dive & Customization",
        "description": "Explore shell types, auto-completion, aliases, history, environment variables ($PATH, $SHELL), and prompt customization ($PS1).",
        "objectives": [
            "Identify different Linux shells (sh, csh, ksh, zsh, bash) and check the active shell with `echo $SHELL`.",
            "Change the login shell using `chsh`.",
            "Harness productivity features: Tab auto-completion, custom aliases (`alias`), and command `history`.",
            "Inspect and configure environment variables using `env` and `export`.",
            "Understand the `$PATH` search variable, check program paths with `which`, and append new directories to `$PATH`.",
            "Customize the interactive shell prompt by configuring `$PS1` with special escape codes (`\\u`, `\\h`, `\\w`, `\\t`)."
        ],
        "key_concepts": [
            {
                "term": "Shell Flavors (sh, csh, ksh, zsh, bash)",
                "explanation": "• **sh (Bourne shell)**: Developed in 1970s, ancestor of modern shells.\n• **bash (Bourne-Again Shell)**: Default on most Linux distributions, featuring aliases, history, and completions.\n• **zsh / csh / ksh**: Alternate shells with unique syntax, theming, and scripting additions."
            },
            {
                "term": "Productivity Powerhouses: Tab & Aliases",
                "explanation": "• **Tab Completion**: Type first few letters of a command, file, or path and press `Tab`. Pressing `Tab` twice lists all matching options.\n• **Aliases**: Create custom shortcuts (e.g., `alias dt='date'` or `alias ll='ls -la'`)."
            },
            {
                "term": "Environment Variables & The `$PATH`",
                "explanation": "Environment variables store session configuration for the shell and child processes. When you type `ls`, Linux doesn't check the entire disk; it looks through directories listed in `$PATH` (colon-separated). To make third-party programs callable from anywhere: `export PATH=$PATH:/opt/mybin`."
            },
            {
                "term": "Customizing the Prompt (`$PS1`)",
                "explanation": "The prompt string is stored in the `$PS1` variable. It supports backslash escapes:\n• `\\u` = Username\n• `\\h` = Hostname\n• `\\w` = Full current working directory (`\\W` for basename only)\n• `\\d` = Date, `\\t` = 24-hr time\n• `\\$` = `#` if root, `$` if regular user."
            }
        ],
        "commands": [
            {
                "cmd": "echo $SHELL",
                "desc": "Print the current user's default login shell.",
                "example": "echo $SHELL\n# Output: /bin/bash",
                "options": "Case-sensitive uppercase"
            },
            {
                "cmd": "chsh -s <shell_path>",
                "desc": "Change login shell (e.g. to /bin/zsh or /bin/bash).",
                "example": "chsh -s /bin/bash",
                "options": "Requires logging in again to take effect"
            },
            {
                "cmd": "alias <shortcut>='<command>'",
                "desc": "Create a command shortcut or alias.",
                "example": "alias dt='date'\nalias ll='ls -lah'",
                "options": "Run `alias` without arguments to see all active shortcuts"
            },
            {
                "cmd": "history",
                "desc": "Display list of previously executed commands with event numbers.",
                "example": "history\n!42   # rerun command #42",
                "options": "`history -c` clears history"
            },
            {
                "cmd": "env",
                "desc": "Print all exported environment variables in current session.",
                "example": "env\nenv | grep USER",
                "options": "Can run a command in modified env"
            },
            {
                "cmd": "export <VAR>=<value>",
                "desc": "Set or export an environment variable to child processes.",
                "example": "export OFFICE=\"caleston\"\nexport PATH=$PATH:/opt/OBS/bin",
                "options": "Add to `~/.bashrc` or `~/.profile` for persistence"
            },
            {
                "cmd": "which <command>",
                "desc": "Locate an executable binary in the `$PATH`.",
                "example": "which ls\nwhich python3\nwhich obs",
                "options": "Returns exit code 1 if not in PATH"
            },
            {
                "cmd": "echo $PS1 / export PS1=...",
                "desc": "Inspect or customize the Bash prompt string.",
                "example": "echo $PS1\nexport PS1='[\\u@\\h \\w]\\$ '",
                "options": "Use escape sequences: \\u, \\h, \\w, \\t, \\d"
            }
        ],
        "exercises": [
            "Check your current shell: `echo $SHELL`.",
            "Create a quick alias: `alias now='date \"+%Y-%m-%d %H:%M:%S\"'` and test running `now`.",
            "Check command history: run `history | tail -n 10`.",
            "View your system search path: run `echo $PATH` and examine the colon-separated paths.",
            "Find where executables live: run `which ls`, `which bash`, `which touch`.",
            "Experiment with a custom prompt in your current terminal session: `export PS1=\"[\\u@\\h \\W]\\$ \"`. Notice how the prompt immediately changes!"
        ]
    },
    "0170-story-section": {
        "title": "Story Section: Bob's First Team Meeting & Enterprise Linux Distros",
        "description": "Join Bob in his first team meeting for Project Mercury, exploring enterprise Linux distributions (Ubuntu, Debian, CentOS, RHEL), cloud VMs, containers, and why deep Linux understanding matters.",
        "objectives": [
            "Understand how Linux is used across modern engineering teams (development, QA, operations, and project management).",
            "Learn the major Linux distribution families (Debian/Ubuntu vs. RHEL/CentOS) and why organizations choose them.",
            "Explore application deployment architectures from on-premise dev servers to cloud VMs and Kubernetes clusters.",
            "Prepare for the hands-on lab environment used throughout the core concepts curriculum."
        ],
        "key_concepts": [
            {
                "term": "Distro Wars in Enterprise IT",
                "explanation": "Organizations choose Linux distributions based on stability, package ecosystems, and support:\n• **Debian / Ubuntu**: Widely loved for developer ergonomics, extensive packages (`apt`), and massive cloud presence.\n• **RHEL / CentOS**: Enterprise industry standards renowned for long-term stability and corporate certification (`yum` / `dnf`)."
            },
            {
                "term": "The Modern Deployment Continuum",
                "explanation": "Applications evolve through stages:\n1. **On-Premise Physical Servers**: Local hardware in company data centers.\n2. **Cloud Virtual Machines (VMs)**: Virtual instances (AWS EC2, GCP Compute Engine, Azure VMs).\n3. **Containers & Microservices**: Docker containers bundling apps with dependencies.\n4. **Kubernetes Clusters**: Managed container orchestration environments."
            },
            {
                "term": "The 'Everything is Connected' Linux Questions",
                "explanation": "As Bob noticed when handling client escalations, working effectively in Linux requires knowing: What is the Kernel? Why are files stored in `/etc`, `/var`, `/usr`, and `/dev`? Understanding these fundamentals is what separates beginner users from confident system engineers."
            },
            {
                "term": "Hands-on Sandbox Environments",
                "explanation": "Real learning happens through practical experimentation. Lab sandboxes provide live Linux environments that can be tested, broken, and recreated cleanly without risking production systems."
            }
        ],
        "commands": [
            {
                "cmd": "cat /etc/os-release",
                "desc": "Display operating system distribution name, version, and family details.",
                "example": "cat /etc/os-release",
                "options": "Available on all modern systemd-based Linux distros"
            },
            {
                "cmd": "hostnamectl",
                "desc": "Query system hostname, operating system, kernel release, and hardware architecture.",
                "example": "hostnamectl",
                "options": "Shows virtualization and chassis info"
            },
            {
                "cmd": "uname -a",
                "desc": "Print complete system and kernel architecture summary.",
                "example": "uname -a",
                "options": "`-r` for kernel release only"
            },
            {
                "cmd": "ls -l /",
                "desc": "List all root directories on the system (/etc, /var, /usr, /dev, /home).",
                "example": "ls -l /",
                "options": "Inspects system hierarchy root"
            }
        ],
        "exercises": [
            "Check your distribution information: run `cat /etc/os-release` or `lsb_release -a`.",
            "Inspect host and architecture information using `hostnamectl`.",
            "Check your current logged-in user: `whoami` and your current shell `echo $SHELL`.",
            "List the top-level root directories on your machine: `ls -l /` and observe directories like `/etc`, `/var`, and `/dev`."
        ]
    },
    "0210-linux-kernel": {
        "title": "The Linux Kernel, Architecture & System Calls",
        "description": "Understand what the Linux Kernel is through the Librarian analogy, monolithic vs modular design, Kernel vs User space, and system calls.",
        "objectives": [
            "Grasp the primary responsibilities of the Linux Kernel (Memory Management, Process Scheduling, Device Drivers, System Calls & Security).",
            "Understand the Monolithic yet Modular architecture of the Linux Kernel.",
            "Inspect the active Kernel version using `uname -r` and decode the version numbering syntax.",
            "Distinguish between privileged Kernel Space (Ring 0) and restricted User Space / Userland (Ring 3).",
            "Learn how User Space applications request hardware operations via System Calls (`open`, `read`, `write`, `getpid`)."
        ],
        "key_concepts": [
            {
                "term": "The College Librarian Analogy",
                "explanation": "• **Librarian** = Linux Kernel.\n• **Books, DVDs & Workstations** = Hardware resources (CPU, RAM, Disks).\n• **Students** = Applications and user processes.\nWithout the librarian, students would hoard books, cause chaos, and starve others of resources. The librarian fairly allocates, tracks, and reclaims resources so every process runs smoothly."
            },
            {
                "term": "4 Major Duties of the Kernel",
                "explanation": "1. **Memory Management**: Keeps track of how much memory is used, by whom, and where.\n2. **Process Management**: Schedules which processes get CPU time, when, and for how long.\n3. **Device Drivers**: Translates requests into electrical hardware instructions.\n4. **System Calls & Security**: Mediates requests between processes and enforces security permissions."
            },
            {
                "term": "Monolithic yet Modular Architecture",
                "explanation": "• **Monolithic**: The entire kernel executes in a single privileged address space for high speed and direct hardware access.\n• **Modular**: Can dynamically load or unload Kernel Modules (`.ko` files) on the fly without rebooting the system."
            },
            {
                "term": "Kernel Space vs. User Space (Userland)",
                "explanation": "• **Kernel Space (Ring 0)**: Strictly reserved for running the kernel core, extensions, and drivers. Unrestricted direct hardware access.\n• **User Space (Ring 3)**: Where user applications (Python, Java, bash, Firefox) execute with restricted access to CPU and RAM to prevent crashes from taking down the OS."
            },
            {
                "term": "System Calls (Syscalls)",
                "explanation": "When an application needs to read a file (e.g. `/etc/os-release`), allocate RAM, or send network packets, it issues a **system call** (`open()`, `read()`, `write()`, `close()`). The CPU transitions from User mode into Kernel mode to fulfill the request safely."
            }
        ],
        "commands": [
            {
                "cmd": "uname -r",
                "desc": "Print the current active Linux Kernel version.",
                "example": "uname -r\n# Output: 5.15.0-72-generic",
                "options": "Format: <kernel>.<major>.<minor>-<patch>-<distro>"
            },
            {
                "cmd": "uname -a",
                "desc": "Display complete kernel and architecture information.",
                "example": "uname -a",
                "options": "`-m` machine arch, `-s` kernel name"
            },
            {
                "cmd": "cat /proc/version",
                "desc": "Inspect kernel compile information and GCC version.",
                "example": "cat /proc/version",
                "options": "Virtual file generated by kernel"
            },
            {
                "cmd": "strace <command>",
                "desc": "Trace system calls invoked by a program (if installed).",
                "example": "strace -c ls",
                "options": "`-c` generates summary count of syscalls"
            }
        ],
        "exercises": [
            "Check your active kernel version: run `uname -r` and break down its version numbers.",
            "View full kernel build details: run `uname -a` and `cat /proc/version`.",
            "Read an OS configuration file that triggers a system call: `cat /etc/os-release`.",
            "Visit [kernel.org](https://kernel.org) in your browser to check the latest stable Linux kernel release."
        ]
    },
    "0220-working-with-hardware": {
        "title": "Working with Hardware, Udev & Superuser Privileges",
        "description": "Explore hardware discovery, udev daemon, dmesg, PCI and block device inspection, CPU/RAM diagnostics, and running commands with sudo.",
        "objectives": [
            "Understand how Linux detects and configures hardware devices via kernel drivers, uevents, and the `udev` daemon.",
            "Inspect boot-time and runtime hardware messages using `dmesg` and the kernel ring buffer.",
            "List and query PCI devices (`lspci`) and block storage devices (`lsblk`).",
            "Decode block device major and minor numbers (driver type vs partition instance).",
            "Analyze CPU architecture (`lscpu`), 32-bit vs 64-bit limits, and calculate total virtual CPUs.",
            "Measure system memory usage with `lsmem` and `free -h`.",
            "Extract full machine hardware reports using `lshw` and understand privilege escalation with `sudo`."
        ],
        "key_concepts": [
            {
                "term": "Dynamic Hardware Lifecycle & `udev`",
                "explanation": "1. Device (e.g. USB disk) is plugged in.\n2. Device driver in kernel space detects change and generates a `uevent`.\n3. User-space daemon `udev` catches the event and dynamically creates a device node in `/dev/` (e.g., `/dev/sdb1`)."
            },
            {
                "term": "Kernel Ring Buffer (`dmesg`)",
                "explanation": "The kernel logs all hardware initialization and driver diagnostics into an in-memory ring buffer. Use `dmesg` to inspect whether attached devices were detected and configured properly."
            },
            {
                "term": "Major vs. Minor Device Numbers",
                "explanation": "In `lsblk` or `ls -l /dev`:\n• **Major number** (left of colon): Identifies the driver type (e.g., `8` represents SCSI/SATA disk driver).\n• **Minor number** (right of colon): Distinguishes the specific physical drive or partition (e.g., `0` for `sda`, `1` for `sda1`)."
            },
            {
                "term": "32-Bit vs. 64-Bit Architecture",
                "explanation": "• **32-Bit CPUs**: Can address $2^{32}$ values (maximum 4 GB of RAM). Limited to 32-bit software.\n• **64-Bit CPUs**: Can address $2^{64}$ values (theoretical 18 Exabytes of RAM). Can run both 32-bit and 64-bit operating systems and applications."
            },
            {
                "term": "Superuser Privileges & `sudo`",
                "explanation": "Hardware inspection utilities (like `lshw`) need direct low-level access. Regular users get incomplete warnings. Prefixing commands with `sudo` ('superuser do') temporarily executes them with root privileges using your own password."
            }
        ],
        "commands": [
            {
                "cmd": "dmesg | less",
                "desc": "View kernel ring buffer messages and boot hardware diagnostics.",
                "example": "dmesg | grep -i usb\ndmesg | tail -n 25",
                "options": "Pipe through `less` or `grep`"
            },
            {
                "cmd": "lspci",
                "desc": "List all PCI devices attached to motherboard slots (NICs, GPUs, RAID).",
                "example": "lspci\nlspci -v",
                "options": "`-v` verbose"
            },
            {
                "cmd": "lsblk",
                "desc": "List block storage devices, physical disks, and partitions.",
                "example": "lsblk\nlsblk -f",
                "options": "`-f` shows filesystems and UUIDs"
            },
            {
                "cmd": "lscpu",
                "desc": "Display CPU architecture, sockets, cores, threads, and vCPUs.",
                "example": "lscpu",
                "options": "Shows 32-bit vs 64-bit modes"
            },
            {
                "cmd": "free -h",
                "desc": "Display total, used, and available system RAM in human-readable units.",
                "example": "free -h\nfree -m",
                "options": "`-h` human-readable, `-m` MB, `-g` GB"
            },
            {
                "cmd": "lsmem --summary",
                "desc": "List online memory ranges and total available memory.",
                "example": "lsmem --summary",
                "options": "Omitting flag shows memory blocks"
            },
            {
                "cmd": "sudo lshw -short",
                "desc": "Generate summary inventory of all system hardware with superuser privileges.",
                "example": "sudo lshw -short",
                "options": "`-short` produces concise hardware table"
            }
        ],
        "exercises": [
            "Check total and available RAM: run `free -h` and `lsmem --summary`.",
            "Inspect your CPU architecture and calculate total vCPUs: run `lscpu` (Sockets × Cores × Threads).",
            "List storage disks and partitions: run `lsblk` and identify major/minor numbers.",
            "List all PCI motherboard peripherals: run `lspci`.",
            "View recent kernel ring buffer messages: `dmesg | tail -n 20`.",
            "Run a hardware inventory using `sudo lshw -short` (or `lshw -short`)."
        ]
    },
    "0250-linux-boot-sequence": {
        "title": "The Linux Boot Sequence & Init Systems",
        "description": "Learn the four stages of the Linux boot process: BIOS/UEFI POST, GRUB2 Bootloader, Kernel Initialization, and Systemd Service Initialization.",
        "objectives": [
            "Trace the four sequential stages of the Linux boot cycle.",
            "Understand BIOS/UEFI Power-On Self-Test (POST) and boot device selection.",
            "Explain the role of GRUB2 (Grand Unified Bootloader v2) in `/boot/`.",
            "Understand kernel decompression, hardware driver initialization, and root filesystem mounting.",
            "Compare modern `systemd` with legacy System V (SysV) init.",
            "Verify the active init system using `ls -l /sbin/init`."
        ],
        "key_concepts": [
            {
                "term": "The 4 Boot Stages Overview",
                "explanation": "1. **BIOS / UEFI POST**: Verifies hardware health (RAM, CPU, board).\n2. **Bootloader (GRUB2)**: Reads boot code from disk sector/partition, presents OS selection, loads compressed kernel.\n3. **Kernel Initialization**: Decompresses into memory, initializes hardware drivers, mounts root `/` filesystem, and launches PID 1 (`init`).\n4. **Service Initialization (`systemd`)**: Starts system services, mounts filesystems, and brings machine to usable login state."
            },
            {
                "term": "GRUB2 (Grand Unified Bootloader v2)",
                "explanation": "The default bootloader for modern Linux distributions. Located in the `/boot` filesystem, it allows dual-booting between operating systems and passing startup parameters to the Linux kernel."
            },
            {
                "term": "Modern `systemd` vs Legacy `SysV init`",
                "explanation": "• **SysV init**: Started daemons strictly sequentially (one by one) using shell scripts in `/etc/init.d/`, resulting in slow boot times.\n• **systemd**: Modern standard across Ubuntu, RHEL, Debian. Parallelizes service startup, uses socket activation, and dramatically speeds up system boot."
            },
            {
                "term": "PID 1: The Parent of All Processes",
                "explanation": "The very first user-space process launched by the kernel is assigned Process ID 1 (`PID 1`). In systemd systems, `/sbin/init` is a symlink pointing directly to `/lib/systemd/systemd`."
            }
        ],
        "commands": [
            {
                "cmd": "ls -l /sbin/init",
                "desc": "Check which init system is running (points to /lib/systemd/systemd).",
                "example": "ls -l /sbin/init",
                "options": "Reveals init symlink"
            },
            {
                "cmd": "systemd-analyze",
                "desc": "Measure total boot time broken down by kernel and userspace.",
                "example": "systemd-analyze",
                "options": "Shows startup time"
            },
            {
                "cmd": "systemd-analyze blame",
                "desc": "List individual services ranked by startup duration.",
                "example": "systemd-analyze blame | head -n 10",
                "options": "Helps find slow boot services"
            },
            {
                "cmd": "journalctl -b",
                "desc": "Inspect system logs from the current boot session.",
                "example": "journalctl -b -p err",
                "options": "`-p err` filters errors only"
            }
        ],
        "exercises": [
            "Check your system's PID 1 init binary: run `ls -l /sbin/init`.",
            "Measure your machine's boot performance: run `systemd-analyze`.",
            "Find which services took the most time to start: run `systemd-analyze blame | head -n 10`.",
            "Inspect system errors logged during the last boot: `journalctl -b -p err`."
        ]
    },
    "0260-runlevels": {
        "title": "Runlevels & Systemd Targets",
        "description": "Master Linux operational modes, comparing SysV runlevels (0-6) with modern Systemd targets (multi-user vs graphical), and switching defaults.",
        "objectives": [
            "Understand operating modes (runlevels) in Linux.",
            "Differentiate between Runlevel 3 (`multi-user.target`) and Runlevel 5 (`graphical.target`).",
            "Check the active runlevel and default systemd target.",
            "Inspect the default target symlink at `/etc/systemd/system/default.target`.",
            "Safely change the system's default boot target using `systemctl set-default`."
        ],
        "key_concepts": [
            {
                "term": "What are Runlevels / Operational Modes?",
                "explanation": "A runlevel defines the state of the machine and what services are active:\n• **Runlevel 0**: Halt / Power off (`poweroff.target`).\n• **Runlevel 1 / Single-User**: Minimal maintenance / rescue mode (`rescue.target`).\n• **Runlevel 3**: Multi-user command-line interface without GUI (`multi-user.target`). Standard for servers.\n• **Runlevel 5**: Full multi-user with graphical display manager (`graphical.target`). Standard for laptops/desktops.\n• **Runlevel 6**: Reboot (`reboot.target`)."
            },
            {
                "term": "SysV Runlevels vs. Systemd Targets",
                "explanation": "In systemd, numbered runlevels are replaced by **Target Units** (`.target` files). For example, `graphical.target` requires display manager services (GDM/LightDM), whereas `multi-user.target` does not, saving RAM and CPU."
            },
            {
                "term": "The `default.target` Symlink",
                "explanation": "During boot, systemd reads `/etc/systemd/system/default.target`. This file is a symbolic link pointing to the desired target under `/lib/systemd/system/`."
            }
        ],
        "commands": [
            {
                "cmd": "runlevel",
                "desc": "Print previous and current SysV runlevel numbers.",
                "example": "runlevel\n# Output: N 5 (or N 3)",
                "options": "N means no previous runlevel"
            },
            {
                "cmd": "systemctl get-default",
                "desc": "Display the current default systemd target.",
                "example": "systemctl get-default\n# Output: graphical.target",
                "options": "Queries default boot mode"
            },
            {
                "cmd": "sudo systemctl set-default <target>",
                "desc": "Change default boot target permanently.",
                "example": "sudo systemctl set-default multi-user.target\nsudo systemctl set-default graphical.target",
                "options": "Updates /etc/systemd/system/default.target symlink"
            },
            {
                "cmd": "sudo systemctl isolate <target>",
                "desc": "Immediately switch target state in current session without rebooting.",
                "example": "sudo systemctl isolate multi-user.target",
                "options": "Stops non-matching services"
            }
        ],
        "exercises": [
            "Check your current operational runlevel: run `runlevel`.",
            "Query your current default systemd target: run `systemctl get-default`.",
            "Inspect the symlink file directly: `ls -l /etc/systemd/system/default.target`.",
            "List all target unit files installed on your system: `systemctl list-unit-files --type=target`."
        ]
    },
    "0270-file-types": {
        "title": "Linux File Types & Identification",
        "description": "Explore the 'Everything is a file' philosophy, regular vs directory vs special files, the 7 file types, and identification using file and ls -l.",
        "objectives": [
            "Comprehend the core Unix/Linux tenet: 'Everything is a file'.",
            "Categorize Linux files into Regular, Directory, and Special file types.",
            "Identify all 7 fundamental Linux file types by their `ls -l` leading character (`-`, `d`, `l`, `c`, `b`, `s`, `p`).",
            "Differentiate between Hard Links and Symbolic Links (Symlinks).",
            "Inspect and determine file types using the `file` command."
        ],
        "key_concepts": [
            {
                "term": "'Everything is a File' in Linux",
                "explanation": "In Linux, virtually every system resource — text documents, directories, serial ports, disks, partitions, inter-process communication sockets, and named pipes — is exposed as an entry in the filesystem tree and read/written using unified file APIs."
            },
            {
                "term": "The 7 Linux File Types & `ls -l` Indicators",
                "explanation": "When running `ls -l`, the very first character reveals the exact file type:\n• `-` **Regular file**: Text, shell scripts, source code, images, executable binaries.\n• `d` **Directory**: Special file storing names and pointers to other files.\n• `l` **Symbolic link**: Shortcut pointer referencing another file path.\n• `c` **Character device**: Unbuffered serial stream hardware (e.g., keyboard, mouse, `/dev/null`, `/dev/tty`).\n• `b` **Block device**: Buffered chunk storage hardware (e.g., hard drives `/dev/sda`, flash disks).\n• `s` **Socket**: Network / IPC endpoint enabling two processes to exchange data.\n• `p` **Named pipe (FIFO)**: Unidirectional first-in-first-out pipe connecting output of one process into another."
            },
            {
                "term": "Symbolic Links vs. Hard Links",
                "explanation": "• **Symbolic Link (`ln -s`)**: A shortcut pointing to a target filename. If target is deleted, link becomes broken/dangling.\n• **Hard Link (`ln`)**: An additional filename entry pointing to the exact same inode and disk data blocks. Deleting one hard link leaves data intact as long as another link exists."
            }
        ],
        "commands": [
            {
                "cmd": "file <path>",
                "desc": "Determine file type by reading binary headers and magic numbers.",
                "example": "file /bin/bash\nfile /etc/passwd\nfile /dev/sda",
                "options": "`-b` brief mode (no filename)"
            },
            {
                "cmd": "ls -l <path>",
                "desc": "Check file type by inspecting the 1st character of the mode string.",
                "example": "ls -l /dev/null\nls -ld /home\nls -l /bin/sh",
                "options": "Inspects 1st character: -, d, l, c, b, s, p"
            },
            {
                "cmd": "ln -s <target> <linkname>",
                "desc": "Create a symbolic (soft) link pointing to another path.",
                "example": "ln -s /etc/os-release os_info.txt",
                "options": "`-s` symbolic"
            },
            {
                "cmd": "ln <target> <linkname>",
                "desc": "Create a hard link sharing the same inode on disk.",
                "example": "ln file1.txt file1_hardlink.txt",
                "options": "Cannot cross filesystem boundaries"
            }
        ],
        "exercises": [
            "Test the `file` utility against various paths: `file /bin/bash`, `file /etc/os-release`, `file /dev/null`.",
            "Inspect character and block devices in `/dev`: `ls -l /dev/null` (character `c`) and `ls -l /dev/sda*` or `/dev/nvme*` (block `b`).",
            "Create a test file and a symbolic link: `touch test_doc.txt && ln -s test_doc.txt test_symlink.txt`.",
            "Run `ls -l test_doc.txt test_symlink.txt` to verify the `l` prefix and `->` pointer, then remove them: `rm test_doc.txt test_symlink.txt`."
        ]
    },
    "0280-filesystem-hierarchy": {
        "title": "Filesystem Hierarchy Standard (FHS)",
        "description": "Navigate the standard Linux directory layout: /, /home, /root, /etc, /opt, /mnt, /media, /tmp, /dev, /usr, /var, and inspect storage with df.",
        "objectives": [
            "Navigate the standard Linux directory tree starting from the root directory `/`.",
            "Understand the distinct purpose of critical system directories (`/etc`, `/opt`, `/tmp`, `/var`, `/usr`, `/dev`).",
            "Contrast `/mnt` (manual temporary mounts) with `/media` (automatic removable media mounts).",
            "Locate logs and variable service data under `/var/log`.",
            "Inspect mounted filesystems, total storage, and disk utilization using `df -h`."
        ],
        "key_concepts": [
            {
                "term": "Single Inverted Tree Structure",
                "explanation": "Unlike Windows which assigns separate drive letters (`C:`, `D:`), Linux organizes everything into a single inverted hierarchical tree beginning at the root directory `/`. All disks, partitions, and removable storage are mounted onto folders inside this single tree."
            },
            {
                "term": "Essential FHS Directories",
                "explanation": "• `/` = Root directory, parent of all other folders.\n• `/root` = Dedicated home directory for the superuser root.\n• `/home/<user>` = User personal workspace folders.\n• `/bin` & `/sbin` = Essential user and system administration executables.\n• `/etc` = Host-specific system and software configuration files.\n• `/opt` = Optional third-party software packages and custom web apps (e.g. Project Mercury).\n• `/mnt` = Temporary mount point for manually mounted filesystems.\n• `/media` = Automatic mount point for removable media (USB drives, external SSDs).\n• `/tmp` = Temporary scratch space; often wiped on reboot.\n• `/dev` = Device node files representing system hardware.\n• `/lib` & `/lib64` = Shared libraries required by binaries in `/bin` and `/sbin`.\n• `/usr` = Userland secondary hierarchy for user applications (`/usr/bin`, `/usr/lib`).\n• `/var` = Variable data that grows dynamically: logs (`/var/log`), caches, mail."
            },
            {
                "term": "Inspecting Storage with `df -h`",
                "explanation": "The `df` (disk filesystem) command displays disk space usage, showing filesystem device paths (`/dev/sda1`), total size, used space, percentage used, and where each filesystem is mounted."
            }
        ],
        "commands": [
            {
                "cmd": "df -h",
                "desc": "Display mounted filesystems, total size, used space, and mount points.",
                "example": "df -h\ndf -h /",
                "options": "`-h` human-readable (GB, MB), `-T` show filesystem type"
            },
            {
                "cmd": "ls -l /",
                "desc": "List all root directories in the Filesystem Hierarchy Standard.",
                "example": "ls -l /",
                "options": "Shows permissions and symlinks"
            },
            {
                "cmd": "du -sh <path>",
                "desc": "Estimate disk space used by a directory.",
                "example": "du -sh /var/log\ndu -sh ~",
                "options": "`-s` summary, `-h` human-readable"
            },
            {
                "cmd": "mount / umount",
                "desc": "Mount or unmount storage devices onto directory mount points.",
                "example": "sudo mount /dev/sdb1 /mnt\nsudo umount /mnt",
                "options": "Requires root/sudo privileges"
            }
        ],
        "exercises": [
            "Inspect all mounted filesystems and available disk space: run `df -h`.",
            "Explore the top-level FHS directory tree: run `ls -l /`.",
            "Inspect system and application configuration files: `ls /etc | head -n 20`.",
            "View where system logs are kept: `ls -l /var/log`.",
            "Estimate disk space consumed by your home directory: `du -sh ~`."
        ]
    },
    "0310-package-management-introduction": {
        "title": "Package Management Fundamentals & Architecture",
        "description": "Understand what packages are, the problem of Dependency Hell, digital signature verification, and the two major packaging ecosystems (Debian vs RPM).",
        "objectives": [
            "Understand what a software package is (compressed archive of binaries, libraries, configs, and manifest metadata).",
            "Learn why package managers were invented: dependency resolution, avoiding 'Dependency Hell', and repository security.",
            "Compare the two dominant Linux packaging ecosystems: Debian family (.deb, dpkg, apt) vs. Red Hat / RPM family (.rpm, rpm, yum, dnf).",
            "Distinguish between Community Enterprise Linux (CentOS) and Commercial Enterprise Linux (RHEL).",
            "Understand low-level local package installers vs high-level repository managers."
        ],
        "key_concepts": [
            {
                "term": "Anatomy of a Software Package",
                "explanation": "A package is a structured archive containing:\n1. Compiled binaries and libraries.\n2. Default configuration files.\n3. Documentation and man pages.\n4. Metadata manifest (package name, version, architecture, maintainer, checksums, and dependency requirements).\n5. Pre-install and post-install configuration scripts."
            },
            {
                "term": "The 'Dependency Hell' Problem",
                "explanation": "Software rarely runs in total isolation; it requires shared libraries and helper utilities. If you manually install a package that depends on Library A, which depends on Library B (version 2), and your system has version 1, everything breaks. Package managers automate resolving, downloading, and ordering this entire tree of dependencies."
            },
            {
                "term": "Package Integrity & Security",
                "explanation": "Package managers use cryptographic checksums (SHA-256) and GPG digital signatures to ensure that packages downloaded across the internet originate from trusted maintainers and have not been altered or tampered with."
            },
            {
                "term": "The Two Big Packaging Families",
                "explanation": "• **Debian Family (Debian, Ubuntu, Linux Mint)**:\n  - Format: `.deb`\n  - Low-Level Tool: `dpkg` (local file installation, no auto-dependencies)\n  - High-Level Tool: `apt` / `apt-get` (repository downloads, automated dependencies)\n• **Red Hat Family (RHEL, CentOS, Fedora)**:\n  - Format: `.rpm`\n  - Low-Level Tool: `rpm` (local file installation, no auto-dependencies)\n  - High-Level Tool: `yum` / `dnf` (repository downloads, automated dependencies)"
            },
            {
                "term": "Community (CentOS) vs. Commercial (RHEL)",
                "explanation": "CentOS is a binary-compatible open-source community rebuild of Red Hat Enterprise Linux (RHEL). RHEL requires a commercial paid subscription but includes enterprise support SLAs, certified security patches, and regulatory compliance assistance."
            }
        ],
        "commands": [
            {
                "cmd": "cat /etc/os-release",
                "desc": "Check distribution ID and family (ID_LIKE=debian or ID_LIKE=rhel).",
                "example": "cat /etc/os-release",
                "options": "Inspects distro packaging family"
            },
            {
                "cmd": "which dpkg apt rpm yum dnf",
                "desc": "Check which package managers are installed in the current environment.",
                "example": "which dpkg apt rpm yum dnf",
                "options": "Prints paths to active utilities"
            }
        ],
        "exercises": [
            "Identify your system's package family: check `cat /etc/os-release` and look at `ID_LIKE` (e.g. `debian` or `rhel`).",
            "Test which package managers are available on your machine: run `which apt`, `which dpkg`, `which yum`, `which rpm`.",
            "Inspect the main repository configuration file on Debian/Ubuntu systems: `cat /etc/apt/sources.list` (or `/etc/yum.repos.d/` on RHEL/CentOS)."
        ]
    },
    "0330-rpm-and-yum": {
        "title": "RPM & YUM Package Management (Red Hat / CentOS)",
        "description": "Master RPM low-level package operations (install, query, verify, erase) and YUM high-level automated repository and dependency management.",
        "objectives": [
            "Understand the 5 core operational modes of the `rpm` utility (Install, Upgrade, Erase/Uninstall, Query, Verify).",
            "Query installed RPM packages and examine package metadata using `rpm -q`, `rpm -qa`, `rpm -qi`.",
            "Verify installed file integrity against the RPM database using `rpm -V`.",
            "Learn how `yum` resolves package dependencies automatically using repository manifests.",
            "Inspect configured repositories in `/etc/yum.repos.d/` (.repo files) and add third-party repos (EPEL, NGINX).",
            "Execute package installations, updates, searches, and removals with `yum`.",
            "Find which package provides an unknown executable with `yum provides <cmd>`."
        ],
        "key_concepts": [
            {
                "term": "The 5 RPM Modes of Operation",
                "explanation": "• **Install**: `rpm -ivh <pkg.rpm>` (i = install, v = verbose, h = print hash `#` progress bar).\n• **Upgrade**: `rpm -Uvh <pkg.rpm>` (U = upgrade existing package, or install if not present).\n• **Erase / Uninstall**: `rpm -e <pkg_name>` (removes the software).\n• **Query**: `rpm -q <pkg_name>` (queries the RPM database stored at `/var/lib/rpm`). Use `-qa` to list all installed, `-qi` for package info, `-ql` to list all installed files.\n• **Verify**: `rpm -V <pkg_name>` (compares installed file sizes, permissions, and checksums against the original package)."
            },
            {
                "term": "RPM's Dependency Limitation",
                "explanation": "The `rpm` utility only knows about the local file you provide it. If `pkg.rpm` requires `libssl.so`, `rpm` errors out and halts. It cannot automatically search the internet or install prerequisites."
            },
            {
                "term": "High-Level Repository Management (`yum` / `dnf`)",
                "explanation": "YUM acts as the intelligent orchestration layer above RPM. When you type `yum install nginx`, YUM:\n1. Queries repository definitions in `/etc/yum.repos.d/*.repo`.\n2. Performs a transaction check and builds a full dependency tree.\n3. Prompts the user with a summary table of packages to be added or upgraded.\n4. Downloads packages and invokes RPM under the hood to perform the installation."
            },
            {
                "term": "Finding Command Providers (`yum provides`)",
                "explanation": "When a command is missing (e.g. `scp` or `dig`), run `yum provides scp` (or `yum provides */dig`). YUM queries all repository catalogs and reveals that `openssh-clients` or `bind-utils` provides that executable."
            }
        ],
        "commands": [
            {
                "cmd": "rpm -ivh <file.rpm>",
                "desc": "Install a local RPM package with verbose hash progress bar.",
                "example": "rpm -ivh nginx-1.20.rpm",
                "options": "`-i` install, `-v` verbose, `-h` hash marks"
            },
            {
                "cmd": "rpm -qa / rpm -qi <pkg>",
                "desc": "Query all installed packages (-qa) or detailed package information (-qi).",
                "example": "rpm -qa | grep python\nrpm -qi bash",
                "options": "`-ql` lists installed files, `-qf <file>` queries which package owns a file"
            },
            {
                "cmd": "rpm -V <pkg>",
                "desc": "Verify installed files against original package checksums in /var/lib/rpm.",
                "example": "rpm -V bash",
                "options": "Prints modified files"
            },
            {
                "cmd": "rpm -e <pkg>",
                "desc": "Erase / uninstall an installed RPM package.",
                "example": "rpm -e telnet",
                "options": "Fails if other packages depend on it"
            },
            {
                "cmd": "yum repolist",
                "desc": "List all configured and active software repositories.",
                "example": "yum repolist",
                "options": "Reads /etc/yum.repos.d/*.repo"
            },
            {
                "cmd": "yum install [-y] <pkg>",
                "desc": "Download and install a package with all dependencies resolved.",
                "example": "yum install -y nginx",
                "options": "`-y` auto-confirms prompts"
            },
            {
                "cmd": "yum update [<pkg>]",
                "desc": "Update a specific package or the entire system if no package specified.",
                "example": "yum update\nyum update telnet",
                "options": "Refreshes and upgrades packages"
            },
            {
                "cmd": "yum remove <pkg>",
                "desc": "Uninstall a package along with any unused dependencies.",
                "example": "yum remove httpd",
                "options": "Cleans dependencies"
            },
            {
                "cmd": "yum provides <command>",
                "desc": "Identify which package provides a specific command or file.",
                "example": "yum provides scp\nyum provides dig",
                "options": "Search remote repo file manifests"
            }
        ],
        "exercises": [
            "Check active repositories on an RPM-based system: `yum repolist` (or `dnf repolist`).",
            "Identify which package supplies the `scp` binary: run `yum provides scp`.",
            "Query all installed RPM packages: `rpm -qa | head -n 25`.",
            "Inspect package details and summary for `bash`: `rpm -qi bash`.",
            "List all files installed on the filesystem by the `bash` package: `rpm -ql bash | head -n 20`."
        ]
    },
    "0340-dpkg-and-apt": {
        "title": "DPKG & APT Package Management (Debian / Ubuntu)",
        "description": "Learn low-level Debian package management with dpkg and high-level automated repository package management with apt.",
        "objectives": [
            "Install and manage local `.deb` packages using the low-level `dpkg` utility.",
            "Inspect installed Debian packages, statuses, and file manifests using `dpkg -l`, `dpkg -s`, and `dpkg -L`.",
            "Understand why `dpkg` requires `apt` to resolve dependencies from repositories.",
            "Configure software repository sources in `/etc/apt/sources.list` and `/etc/apt/sources.list.d/`.",
            "Update local package indexes with `sudo apt update` and apply security updates with `sudo apt upgrade`.",
            "Install, remove, search, and list packages using `apt install`, `apt remove`, `apt search`, and `apt list`."
        ],
        "key_concepts": [
            {
                "term": "Low-Level Debian Installer: `dpkg`",
                "explanation": "The core tool for unpacking and installing `.deb` archives on Debian/Ubuntu systems:\n• `dpkg -i <file.deb>`: Installs or upgrades a local `.deb` file.\n• `dpkg -r <pkg_name>`: Removes the package.\n• `dpkg -l`: Lists installed packages.\n• `dpkg -s <pkg_name>`: Shows status and metadata.\n• `dpkg -L <pkg_name>`: Lists all files installed on disk by the package.\nLike RPM, `dpkg` does not resolve dependencies from remote mirrors."
            },
            {
                "term": "High-Level Repository Manager: `apt`",
                "explanation": "The Advanced Package Tool (`apt`) communicates with software mirrors across HTTP/HTTPS/FTP, resolves dependency graphs, downloads necessary `.deb` files, and invokes `dpkg` under the hood."
            },
            {
                "term": "Repository Sources (`/etc/apt/sources.list`)",
                "explanation": "Debian and Ubuntu define mirrors in `/etc/apt/sources.list` and `/etc/apt/sources.list.d/*.list`:\n`deb http://archive.ubuntu.com/ubuntu/ jammy main restricted universe multiverse`\n• `main`: Officially supported open-source software.\n• `restricted`: Officially supported proprietary drivers.\n• `universe`: Community-maintained open-source software.\n• `multiverse`: Unsupported software with licensing restrictions."
            },
            {
                "term": "`apt update` vs. `apt upgrade`",
                "explanation": "• `apt update`: Synchronizes local index files from remote repositories. It updates your list of *what versions exist*, but installs zero packages.\n• `apt upgrade`: Downloads and installs newer versions of all currently installed packages based on the updated indexes."
            }
        ],
        "commands": [
            {
                "cmd": "dpkg -i <file.deb>",
                "desc": "Install or upgrade a local Debian (.deb) package.",
                "example": "sudo dpkg -i package.deb",
                "options": "Does not fetch dependencies"
            },
            {
                "cmd": "dpkg -l [<pattern>]",
                "desc": "List installed packages matching a pattern.",
                "example": "dpkg -l | grep python",
                "options": "Shows package version and status"
            },
            {
                "cmd": "dpkg -s <pkg>",
                "desc": "Display status and metadata of an installed package.",
                "example": "dpkg -s bash",
                "options": "Inspects status database"
            },
            {
                "cmd": "dpkg -L <pkg>",
                "desc": "List all filesystem files installed by a package.",
                "example": "dpkg -L curl",
                "options": "Lists absolute paths"
            },
            {
                "cmd": "sudo apt update",
                "desc": "Resynchronize package index files from configured repositories in sources.list.",
                "example": "sudo apt update",
                "options": "Run before installing/upgrading"
            },
            {
                "cmd": "sudo apt upgrade",
                "desc": "Install newest versions of all packages currently installed on the system.",
                "example": "sudo apt upgrade -y",
                "options": "`-y` auto-confirms prompts"
            },
            {
                "cmd": "sudo apt install <pkg>",
                "desc": "Download and install package along with all necessary dependencies.",
                "example": "sudo apt install -y nginx",
                "options": "Resolves dependency trees automatically"
            },
            {
                "cmd": "sudo apt remove <pkg>",
                "desc": "Remove an installed package while preserving its configuration files.",
                "example": "sudo apt remove nginx",
                "options": "Use `apt purge` to remove configs too"
            },
            {
                "cmd": "apt search <keyword>",
                "desc": "Search repository package names and descriptions for a keyword.",
                "example": "apt search htop",
                "options": "Provides concise, readable output"
            },
            {
                "cmd": "apt list --installed",
                "desc": "List all packages currently installed on the system.",
                "example": "apt list --installed | grep git",
                "options": "Can filter with `--upgradable`"
            }
        ],
        "exercises": [
            "Refresh your system's package catalog: run `sudo apt update`.",
            "Search for a system utility in the repository: `apt search htop` or `apt search curl`.",
            "Inspect package information before installing: `apt show curl`.",
            "Install a lightweight utility: `sudo apt install -y htop`.",
            "Verify installation using `dpkg`: run `dpkg -s htop` and `dpkg -L htop`.",
            "Clean up test package: `sudo apt remove -y htop`."
        ]
    },
    "0350-apt-vs-apt-get": {
        "title": "APT vs. APT-GET: Key Differences & Best Practices",
        "description": "Compare modern user-friendly apt against traditional apt-get and apt-cache, and learn when to use each in daily terminal work vs scripting.",
        "objectives": [
            "Understand why the `apt` command was introduced as a modern, unified CLI front-end.",
            "Compare terminal output, progress bars, and feedback between `apt` and `apt-get`.",
            "Understand the consolidation of `apt-get` and `apt-cache` into a single `apt` utility.",
            "Know the industry best practice: `apt` for interactive interactive command line; `apt-get` for automated bash scripts."
        ],
        "key_concepts": [
            {
                "term": "Why `apt` Was Introduced",
                "explanation": "Historically, Debian and Ubuntu required separate utilities for package operations:\n• `apt-get` for installation, upgrades, and removals.\n• `apt-cache` for searching and inspecting package metadata.\n• `dpkg` for low-level local package management.\nThe `apt` command combines the most frequently used commands from `apt-get` and `apt-cache` into one clean, human-friendly interface."
            },
            {
                "term": "Modern User Experience in `apt`",
                "explanation": "• **Progress Bar**: When downloading and unpacking packages, `apt` displays an interactive percentage progress bar at the bottom of the terminal.\n• **Cleaner Search**: `apt search` outputs color-coded package names, versions, and concise summaries without verbose junk.\n• **Upgrade Reminders**: Tells you directly how many packages can be upgraded after `apt update`."
            },
            {
                "term": "When to Use `apt` vs. `apt-get`",
                "explanation": "• **Interactive Terminal**: Always use `apt`. It is designed for human consumption, providing intuitive output and helpful formatting.\n• **Shell Scripts, CI/CD, & Dockerfiles**: Always use `apt-get` (e.g. `apt-get update && apt-get install -y --no-install-recommends ...`). `apt-get` provides a stable CLI interface across decades with output designed for non-interactive machine logging."
            },
            {
                "term": "Command Rosetta Stone",
                "explanation": "• `apt install` $\\leftrightarrow$ `apt-get install`\n• `apt remove` $\\leftrightarrow$ `apt-get remove`\n• `apt purge` $\\leftrightarrow$ `apt-get purge`\n• `apt update` $\\leftrightarrow$ `apt-get update`\n• `apt upgrade` $\\leftrightarrow$ `apt-get upgrade`\n• `apt search` $\\leftrightarrow$ `apt-cache search`\n• `apt show` $\\leftrightarrow$ `apt-cache show`\n• `apt autoremove` $\\leftrightarrow$ `apt-get autoremove`"
            }
        ],
        "commands": [
            {
                "cmd": "apt search <keyword>",
                "desc": "Search repository package names and descriptions with clean formatting.",
                "example": "apt search telnet",
                "options": "Human-friendly output"
            },
            {
                "cmd": "apt show <pkg>",
                "desc": "Display comprehensive package information, maintainer, size, and dependencies.",
                "example": "apt show bash",
                "options": "Replaces legacy `apt-cache show`"
            },
            {
                "cmd": "apt list --upgradable",
                "desc": "List all installed packages that have newer versions available in repositories.",
                "example": "apt list --upgradable",
                "options": "Checks against updated indexes"
            },
            {
                "cmd": "sudo apt autoremove",
                "desc": "Automatically remove orphaned packages that were installed as dependencies but are no longer needed.",
                "example": "sudo apt autoremove -y",
                "options": "Frees up disk space safely"
            }
        ],
        "exercises": [
            "Compare package search outputs: run `apt search telnet` vs `apt-cache search telnet` and observe the formatting difference.",
            "Check which installed packages have available updates: `apt list --upgradable`.",
            "Inspect full package metadata: `apt show bash`.",
            "Run an autoremove simulation to inspect orphaned packages: `sudo apt autoremove --dry-run`."
        ]
    },
    "0380-story-section": {
        "slug": "story_section",
        "title": "Story Section: Project Mercury Escalation & Migration Requirements",
        "description": "Join Bob in his high-stakes weekly team meeting with Andrew and Amira, facing project escalations, priority alignment, and preparing to migrate Python/Django code to Linux.",
        "objectives": [
            "Understand project priorities and navigating cross-project escalations in engineering teams.",
            "Identify the technical steps required to migrate application code and datasets from Windows to Linux.",
            "Prepare for file archival (tar), compression (gzip), searching (find/grep), I/O redirection, and editing (vim)."
        ],
        "key_concepts": [
            {
                "term": "Realities of Engineering Prioritization",
                "explanation": "In software projects, managing time between primary project deliverables and third-party support requests is critical. Andrew clarifies to Bob that delivering the core application demonstration for Project Mercury takes precedent over side escalations."
            },
            {
                "term": "Cross-Platform Migration Challenges",
                "explanation": "Migrating a web application (like Django) from Windows to Linux requires:\n1. Copying and archiving file trees.\n2. Decompressing and extracting packages.\n3. Modifying configuration files and system environment variables.\n4. Managing Linux file permissions and dependencies."
            },
            {
                "term": "Essential Shell Power Tools",
                "explanation": "Deploying and managing code on Linux servers requires mastering five core shell capabilities: archiving (`tar`), compression (`gzip`), search (`find`, `grep`), stream redirection (`>`, `|`), and command-line text editing (`vi`/`vim`)."
            }
        ],
        "commands": [
            {
                "cmd": "tar --help",
                "desc": "Display summary manual of tar archive and tape operations.",
                "example": "tar --help",
                "options": "Shows compression and packaging options"
            },
            {
                "cmd": "grep --help",
                "desc": "Display options for pattern matching and regular expressions.",
                "example": "grep --help",
                "options": "Shows search flags"
            },
            {
                "cmd": "which vi vim",
                "desc": "Verify installed console text editors.",
                "example": "which vi vim",
                "options": "Checks system editor paths"
            }
        ],
        "exercises": [
            "Check available archiving utilities on your system: `which tar gzip bzip2 xz`.",
            "Check available file search utilities: `which grep find locate`.",
            "Verify which terminal text editors are installed: `which vi vim nano`."
        ]
    },
    "0410-file-compression-and-archival": {
        "title": "File Compression & Archival (tar, gzip, bzip2, xz)",
        "description": "Inspect disk usage with du, bundle files with tar, compare compression algorithms (gzip, bzip2, xz), and view archives with zcat.",
        "objectives": [
            "Inspect file and directory disk consumption using `du -sh` and `ls -lh`.",
            "Bundle files and directories into tar archives ('tarballs') using `tar -cvf`.",
            "Inspect tarball contents without extracting using `tar -tvf`.",
            "Extract tar archives safely using `tar -xvf`.",
            "Compare compression algorithms: `gzip` (.gz), `bzip2` (.bz2), and `xz` (.xz) for speed vs compression ratio.",
            "Create and extract compressed tarballs in a single command (`tar -czvf` / `tar -xzvf`).",
            "Inspect compressed files without extracting using `zcat`, `bzcat`, and `xzcat`."
        ],
        "key_concepts": [
            {
                "term": "Archiving vs. Compression",
                "explanation": "• **Archiving (`tar`)**: Gathers multiple files, directories, and permissions into a single container file called a tarball without shrinking data size.\n• **Compression (`gzip`, `bzip2`, `xz`)**: Employs mathematical algorithms to remove redundancy and reduce file size on disk."
            },
            {
                "term": "The Anatomy of `tar` Flags",
                "explanation": "• `-c`: Create a new archive.\n• `-x`: Extract files from an archive.\n• `-t`: Table of contents (list files inside archive without extracting).\n• `-v`: Verbose (list files as they are processed).\n• `-f`: File name of the archive (must be followed immediately by archive path).\n• `-z`: Filter archive through `gzip` (.tar.gz).\n• `-j`: Filter archive through `bzip2` (.tar.bz2).\n• `-J`: Filter archive through `xz` (.tar.xz)."
            },
            {
                "term": "Compression Algorithms Compared",
                "explanation": "• **gzip (`.gz`)**: Fastest compression and decompression speed; industry standard for general files.\n• **bzip2 (`.bz2`)**: Higher compression ratio than gzip, but uses more CPU time.\n• **xz (`.xz`)**: Highest compression ratio; creates the smallest files; ideal for OS releases and kernel packages."
            },
            {
                "term": "Reading Without Decompressing (`zcat`, `bzcat`, `xzcat`)",
                "explanation": "Utilities like `zcat` read and display compressed text files directly into stdout without decompressing them to disk, saving space and time."
            }
        ],
        "commands": [
            {
                "cmd": "du -sh <path>",
                "desc": "Display human-readable disk space usage for a directory or file.",
                "example": "du -sh /var/log\ndu -sh ~",
                "options": "`-s` summary, `-h` human-readable, `-sk` kilobytes"
            },
            {
                "cmd": "tar -cvf <archive.tar> <files...>",
                "desc": "Create a new uncompressed tar archive from files or directories.",
                "example": "tar -cvf project_backup.tar src/ assets/",
                "options": "`-c` create, `-v` verbose, `-f` filename"
            },
            {
                "cmd": "tar -tvf <archive.tar>",
                "desc": "List the contents of an archive without extracting.",
                "example": "tar -tvf project_backup.tar",
                "options": "`-t` table of contents"
            },
            {
                "cmd": "tar -xvf <archive.tar>",
                "desc": "Extract all contents from a tar archive into the current directory.",
                "example": "tar -xvf project_backup.tar -C /tmp/restore",
                "options": "`-x` extract, `-C <dir>` target folder"
            },
            {
                "cmd": "tar -czvf <archive.tar.gz> <files...>",
                "desc": "Create a gzip-compressed tar archive in a single operation.",
                "example": "tar -czvf project.tar.gz my_app/",
                "options": "`-z` uses gzip compression"
            },
            {
                "cmd": "tar -xzvf <archive.tar.gz>",
                "desc": "Extract a gzip-compressed tar archive.",
                "example": "tar -xzvf project.tar.gz",
                "options": "`-z` decompresses with gzip"
            },
            {
                "cmd": "gzip <file> / gunzip <file.gz>",
                "desc": "Compress or decompress a single file with gzip algorithm.",
                "example": "gzip database.sql\ngunzip database.sql.gz",
                "options": "Appends/removes `.gz` extension"
            },
            {
                "cmd": "zcat <file.gz>",
                "desc": "Display contents of a gzip-compressed file directly on screen.",
                "example": "zcat /var/log/syslog.1.gz | head -n 25",
                "options": "Also `bzcat` (.bz2), `xzcat` (.xz)"
            }
        ],
        "exercises": [
            "Check disk consumption of your home directory: `du -sh ~`.",
            "Create a practice directory with sample files: `mkdir -p ~/archive_lab && touch ~/archive_lab/file{1..3}.txt`.",
            "Package and compress the directory into a tarball: `tar -czvf ~/backup.tar.gz -C ~ archive_lab`.",
            "List the files inside the tarball without uncompressing: `tar -tvf ~/backup.tar.gz`.",
            "Extract the backup into a new directory: `mkdir -p ~/restored_lab && tar -xzvf ~/backup.tar.gz -C ~/restored_lab`.",
            "Clean up practice files: `rm -rf ~/archive_lab ~/backup.tar.gz ~/restored_lab`."
        ]
    },
    "0415-searching-for-files-and-patterns": {
        "title": "Searching Files & Patterns (locate, find, grep)",
        "description": "Locate files dynamically across the filesystem with find, query the index with locate, and search file content with grep.",
        "objectives": [
            "Search indexed filesystem databases with `locate` and update the database with `sudo updatedb`.",
            "Perform live, dynamic filesystem searches with `find` by name, type, and size.",
            "Search text and code inside files using `grep`.",
            "Use essential grep flags: case-insensitivity (`-i`), recursive directory searching (`-r`), inverted matching (`-v`), and exact whole words (`-w`).",
            "Display surrounding context lines using `-A` (after), `-B` (before), and `-C` (context)."
        ],
        "key_concepts": [
            {
                "term": "`locate` vs. `find`",
                "explanation": "• **`locate`**: Ultra-fast searching by querying a pre-indexed database (`mlocate.db`). If a file was created moments ago, run `sudo updatedb` first to refresh the index.\n• **`find`**: Real-time disk walk starting from a specified root path. Guaranteed up-to-the-second accuracy with rich filters (`-type`, `-size`, `-mtime`)."
            },
            {
                "term": "`grep` (Global Regular Expression Print)",
                "explanation": "The quintessential Linux tool for scanning text and returning lines that match a regular expression or keyword."
            },
            {
                "term": "Essential `grep` Options",
                "explanation": "• `-i`: Case-insensitive search (matches `error`, `Error`, `ERROR`).\n• `-r`: Recursive search across all subdirectories.\n• `-v`: Invert match (prints lines that do *not* contain pattern; great for stripping comments `#`).\n• `-w`: Match whole words only (prevents matching `exam` inside `examples`).\n• `-n`: Print line numbers of matches."
            },
            {
                "term": "Contextual Search with `-A` and `-B`",
                "explanation": "Often the line *above* or *below* an error contains the root cause:\n• `-A <N>`: Print N lines After matching line.\n• `-B <N>`: Print N lines Before matching line.\n• `-C <N>`: Print N lines of Context (both before and after)."
            }
        ],
        "commands": [
            {
                "cmd": "locate <filename>",
                "desc": "Search mlocate database for files matching pattern instantly.",
                "example": "locate city.txt\nlocate nginx.conf",
                "options": "Fast indexed search"
            },
            {
                "cmd": "sudo updatedb",
                "desc": "Refresh the mlocate database index from filesystem.",
                "example": "sudo updatedb",
                "options": "Requires superuser privileges"
            },
            {
                "cmd": "find <path> -name \"<pattern>\"",
                "desc": "Search live filesystem tree for files matching name pattern.",
                "example": "find /var/log -name \"*.log\"\nfind . -name \"city.txt\"",
                "options": "`-iname` case-insensitive, `-type f` files, `-type d` dirs"
            },
            {
                "cmd": "grep -i \"<pattern>\" <file>",
                "desc": "Search file for pattern ignoring case sensitivity.",
                "example": "grep -i \"error\" /var/log/syslog",
                "options": "`-i` ignore case"
            },
            {
                "cmd": "grep -r \"<pattern>\" <dir>",
                "desc": "Recursively search all files inside a directory.",
                "example": "grep -rn \"def main\" src/",
                "options": "`-r` recursive, `-n` line numbers"
            },
            {
                "cmd": "grep -v \"<pattern>\" <file>",
                "desc": "Invert search: display all lines that DO NOT match pattern.",
                "example": "grep -v \"^#\" /etc/hosts\ngrep -v \"^$\" config.ini",
                "options": "Filters out comments and empty lines"
            },
            {
                "cmd": "grep -w \"<word>\" <file>",
                "desc": "Match whole word boundaries only.",
                "example": "grep -w \"exam\" notes.txt",
                "options": "Excludes 'examples' or 'examine'"
            },
            {
                "cmd": "grep -A <N> -B <N> \"<pattern>\" <file>",
                "desc": "Print N lines after (-A) and before (-B) matching pattern.",
                "example": "grep -A 2 -B 1 \"FAIL\" test.log",
                "options": "Shows context around errors"
            }
        ],
        "exercises": [
            "Find all configuration files in `/etc`: `find /etc -name \"*.conf\" 2>/dev/null | head -n 15`.",
            "Search for your username in `/etc/passwd`: `grep $USER /etc/passwd`.",
            "Filter out comment lines from `/etc/hosts`: `grep -v \"^#\" /etc/hosts`.",
            "Create a test file with sample lines and test whole-word matching: `echo -e \"exam\\nexamples\" > test.txt && grep -w \"exam\" test.txt`.",
            "Test context output: `grep -A 1 -B 1 \"exam\" test.txt`.",
            "Clean up: `rm test.txt`."
        ]
    },
    "0420-io-redirection": {
        "title": "I/O Redirection & Command-Line Pipes",
        "description": "Master standard streams (stdin, stdout, stderr), redirection operators (>, >>, 2>, 2>&1), null device bit-bucket, pipes (|), and tee.",
        "objectives": [
            "Understand the three standard Linux I/O streams: standard input (stdin, 0), standard output (stdout, 1), and standard error (stderr, 2).",
            "Redirect and overwrite output to files using `>`.",
            "Append output to existing files using `>>`.",
            "Separate and capture error messages with `2>` and `2>>`.",
            "Discard unwanted error output using `/dev/null` (the 'bit bucket').",
            "Combine `stdout` and `stderr` into a single destination using `&>` or `2>&1`.",
            "Connect commands into powerful processing pipelines using the pipe operator `|`.",
            "Split output to screen and file simultaneously with `tee` and `tee -a`."
        ],
        "key_concepts": [
            {
                "term": "The 3 Standard Streams",
                "explanation": "Every process launched in Linux automatically opens three standard data streams:\n• **stdin (0)**: Standard Input (keyboard stream by default).\n• **stdout (1)**: Standard Output (terminal display for successful command output).\n• **stderr (2)**: Standard Error (terminal display dedicated to warning and error logs)."
            },
            {
                "term": "Overwrite (`>`) vs. Append (`>>`)",
                "explanation": "• `echo \"Hello\" > file.txt`: Wipes existing file content and writes new text.\n• `echo \"World\" >> file.txt`: Keeps existing content and appends new text at the end."
            },
            {
                "term": "Redirecting Errors (`2>`) & The Bit Bucket (`/dev/null`)",
                "explanation": "Errors are tagged with file descriptor `2`. Running `cmd 2> error.log` isolates errors from standard output. If you want to suppress permission denied warnings completely: `find / -name \"*.log\" 2> /dev/null`."
            },
            {
                "term": "Command-Line Pipes (`|`)",
                "explanation": "Pipes connect programs in memory without writing temporary files: stdout of Command 1 becomes stdin of Command 2 (`cat /var/log/syslog | grep error | wc -l`)."
            },
            {
                "term": "Splitting Output with `tee`",
                "explanation": "The `tee` command acts as a T-splitter: it writes output to a file on disk while simultaneously printing it to the terminal screen. Use `-a` to append."
            }
        ],
        "commands": [
            {
                "cmd": "<cmd> > <file>",
                "desc": "Redirect standard output (stdout) to a file, overwriting existing content.",
                "example": "echo \"System operational\" > status.txt",
                "options": "Creates file if missing"
            },
            {
                "cmd": "<cmd> >> <file>",
                "desc": "Append standard output (stdout) to the end of a file.",
                "example": "date >> status.txt",
                "options": "Preserves existing lines"
            },
            {
                "cmd": "<cmd> 2> <file>",
                "desc": "Redirect standard error (stderr) to a file.",
                "example": "ls /root 2> error.log",
                "options": "Captures error messages only"
            },
            {
                "cmd": "<cmd> 2> /dev/null",
                "desc": "Suppress all error messages by dumping into the null device bit-bucket.",
                "example": "find / -name \"*.conf\" 2> /dev/null",
                "options": "Silences permission denied warnings"
            },
            {
                "cmd": "<cmd> &> <file>",
                "desc": "Redirect both stdout and stderr together into a single file.",
                "example": "make &> build.log",
                "options": "Equivalent to `> file 2>&1`"
            },
            {
                "cmd": "<cmd1> | <cmd2>",
                "desc": "Pipe stdout of cmd1 into stdin of cmd2.",
                "example": "cat /etc/passwd | grep -i bash | wc -l",
                "options": "Can chain multiple pipes"
            },
            {
                "cmd": "<cmd> | tee <file>",
                "desc": "Output to terminal screen and write to file at the same time.",
                "example": "uname -a | tee system_info.txt",
                "options": "`-a` appends instead of overwriting"
            }
        ],
        "exercises": [
            "Write system info to a new file: `echo \"Linux Host: $(hostname)\" > host_report.txt`.",
            "Append current timestamp: `date >> host_report.txt && cat host_report.txt`.",
            "Suppress permission errors while searching root: `find /etc -name \"*.conf\" 2> /dev/null | head -n 10`.",
            "Build a pipeline counting how many users use bash: `grep \"bash\" /etc/passwd | wc -l`.",
            "Test the `tee` splitter: `df -h | tee disk_report.txt` and verify file exists.",
            "Clean up test files: `rm host_report.txt disk_report.txt`."
        ]
    },
    "0430-vi-editor": {
        "title": "Working with Text Files: The Vi / Vim Editor",
        "description": "Master terminal-based text editing in vi/vim: Command mode, Insert mode, Last-line mode, cursor movement, copy/paste (yy/p), delete (dd), undo/redo, search, and save/exit (:wq, :q!).",
        "objectives": [
            "Understand why terminal-based text editors are essential for remote server management and scripting.",
            "Seamlessly navigate the three operational modes: Command Mode, Insert Mode, and Last Line Mode.",
            "Use keyboard navigation keys (h, j, k, l) and word movement.",
            "Insert and append text using i, a, o, O, I, A.",
            "Copy (yank) lines with yy and paste them with p.",
            "Delete characters (x), single lines (dd), and multiple lines (d3d).",
            "Undo mistakes with u and redo with Ctrl + R.",
            "Search files using forward slash /pattern and repeat with n/N.",
            "Save and quit reliably using :w, :q, :wq, and :q!."
        ],
        "key_concepts": [
            {
                "term": "The Modal Nature of Vi / Vim",
                "explanation": "Vi operates as a modal editor. Unlike basic editors (like Notepad or Nano) where typing immediately enters text, Vi starts in **Command Mode** where keystrokes trigger editing commands. You explicitly toggle into **Insert Mode** to type, and return to Command Mode with `Esc`."
            },
            {
                "term": "The 3 Primary Modes",
                "explanation": "1. **Command Mode** (Default upon opening): Move cursor, copy lines (`yy`), paste (`p`), delete lines (`dd`), undo (`u`), initiate search (`/`).\n2. **Insert Mode** (Entered via `i`, `a`, `o`): Write and edit text content. Exit back to Command Mode with `Esc`.\n3. **Last Line / Ex Mode** (Entered via `:` in Command mode): Command bar at bottom of terminal. Save (`:w`), quit (`:q`), save & exit (`:wq`), quit without saving (`:q!`)."
            },
            {
                "term": "Command Mode Navigation & Editing Shortcuts",
                "explanation": "• `h`, `j`, `k`, `l`: Left, Down, Up, Right.\n• `yy`: Yank (copy) current line.\n• `p`: Paste copied line below cursor.\n• `dd`: Delete (cut) current line (`d3d` deletes 3 lines).\n• `x`: Delete single character under cursor.\n• `u`: Undo last action (`Ctrl + R` = Redo).\n• `/pattern`: Search forward (`n` = next match, `N` = previous match).\n• `ZZ`: Fast shortcut in Command mode to save and exit."
            },
            {
                "term": "Vi vs. Vim",
                "explanation": "Vim ('Vi IMproved') is an enhanced drop-in replacement for the original 1976 Unix `vi` editor. It adds syntax highlighting, visual selection modes, multiple undo levels, and plugins. In modern Linux distributions, `/usr/bin/vi` is a symbolic link pointing to `vim.basic`."
            }
        ],
        "commands": [
            {
                "cmd": "vi <filename> / vim <filename>",
                "desc": "Open or create a file in the vi/vim text editor.",
                "example": "vi app.py\nvim /etc/nginx/nginx.conf",
                "options": "Starts in Command mode by default"
            },
            {
                "cmd": "i / a / o",
                "desc": "Switch from Command Mode into Insert Mode.",
                "example": "i (insert before cursor)\na (append after cursor)\no (open new line below)",
                "options": "Press `Esc` to return to Command mode"
            },
            {
                "cmd": "yy / p",
                "desc": "Yank (copy) current line, and paste below cursor in Command Mode.",
                "example": "yy\np",
                "options": "Use `p` to paste below, `P` to paste above"
            },
            {
                "cmd": "dd / d<N>d",
                "desc": "Delete (cut) current line, or delete N lines in Command Mode.",
                "example": "dd\nd5d",
                "options": "Deletes lines into buffer"
            },
            {
                "cmd": "u / Ctrl+R",
                "desc": "Undo last action / Redo undone action in Command Mode.",
                "example": "u\nCtrl+R",
                "options": "Multi-level undo supported in vim"
            },
            {
                "cmd": "/<pattern>",
                "desc": "Search forward for pattern. Press `n` for next match, `N` for previous.",
                "example": "/listen\n/server_name",
                "options": "Use `?` to search backwards"
            },
            {
                "cmd": ":w / :q / :wq / :q!",
                "desc": "Last line commands: Save (:w), Quit (:q), Save & Quit (:wq), Force Quit without saving (:q!).",
                "example": ":wq\n:q!",
                "options": "Press `:` in Command mode"
            }
        ],
        "exercises": [
            "Open a new practice document: `vi practice_notes.txt`.",
            "Type `i` to enter Insert Mode. Type 3 lines describing your Linux learning so far.",
            "Press `Esc` to exit to Command Mode.",
            "Move cursor to line 1 and press `yy` to copy it. Move to bottom and press `p` to paste.",
            "Delete a line with `dd`. Undo the change with `u`.",
            "Save and exit: type `:wq` and press Enter.",
            "Verify file content: `cat practice_notes.txt`, then remove it: `rm practice_notes.txt`."
        ]
    },
    "0600-story-section": {
        "slug": "story_section",
        "title": "Story Section: Network Issue & Troubleshooting with Jacqui",
        "description": "Join Bob as he hits a network blockage accessing the internal software repository (caleston-repos), opens a ticket, and pairs with network engineer Jacqui at Desk 8A-052 to diagnose DNS and connectivity.",
        "objectives": [
            "Understand real-world enterprise IT support workflows and ticketing (ServiceNow).",
            "Recognize common DNS errors such as DNS_PROBE_FINISHED_NXDOMAIN.",
            "Distinguish between file-based host resolution (/etc/hosts) and network-based DNS lookup.",
            "Establish a structured, bottom-up troubleshooting methodology for network connectivity issues."
        ],
        "key_concepts": [
            {
                "term": "Enterprise Support & Collaboration",
                "explanation": "When unexpected network errors occur, opening clear IT support tickets (e.g. in ServiceNow) and collaborating across teams (such as meeting Jacqui from Network Support at Desk 8A-052) accelerates root-cause analysis."
            },
            {
                "term": "DNS_PROBE_FINISHED_NXDOMAIN",
                "explanation": "This browser error indicates 'Non-Existent Domain' (NXDOMAIN). The client resolver queried DNS, but the DNS server has no record for that domain name. Jacqui observes that 'http://caleston-repos' was an incomplete name, whereas 'http://caleston-repos-01' is the valid internal host."
            },
            {
                "term": "File-Based vs. Network-Based Resolution",
                "explanation": "Static hostname-to-IP mappings configured directly on a single machine (e.g., inside `/etc/hosts`) only resolve on that local machine. In contrast, enterprise DNS servers resolve names centrally for every client in the network."
            }
        ],
        "commands": [
            {
                "cmd": "ping <host/ip>",
                "desc": "Send ICMP ECHO_REQUEST packets to test network reachability.",
                "example": "ping -c 3 8.8.8.8",
                "options": "`-c <count>` limits number of ping packets"
            },
            {
                "cmd": "hostname",
                "desc": "Show or temporarily change the system's network name.",
                "example": "hostname",
                "options": "`-I` shows all network IP addresses"
            },
            {
                "cmd": "curl -I <url>",
                "desc": "Fetch HTTP response headers to test web service availability.",
                "example": "curl -I http://caleston-repos-01",
                "options": "`-I` fetches headers only, `--connect-timeout <sec>` limits wait"
            }
        ],
        "exercises": [
            "Test local loopback reachability: `ping -c 3 127.0.0.1`.",
            "Test internet connectivity to a public IP: `ping -c 3 8.8.8.8`.",
            "Check your current machine hostname: `hostname`.",
            "View local name resolution mappings: `cat /etc/hosts`."
        ]
    },
    "0620-dns": {
        "slug": "dns_and_name_resolution",
        "title": "DNS & Name Resolution in Linux",
        "description": "Master name resolution from /etc/hosts to central DNS servers: configure /etc/resolv.conf, control resolution priority in /etc/nsswitch.conf, configure search domains, DNS record types (A, AAAA, CNAME), and test with nslookup and dig.",
        "objectives": [
            "Understand how Linux maps hostnames to IP addresses via `/etc/hosts`.",
            "Configure remote DNS nameservers in `/etc/resolv.conf`.",
            "Control resolution search order (`files dns`) in `/etc/nsswitch.conf`.",
            "Configure internal search domains (`search mycompany.com`) for short-name resolution.",
            "Differentiate DNS record types: `A` (IPv4), `AAAA` (IPv6), and `CNAME` (canonical name alias).",
            "Test and diagnose DNS queries using `nslookup` and `dig`."
        ],
        "key_concepts": [
            {
                "term": "Local Name Resolution (`/etc/hosts`)",
                "explanation": "Before DNS, systems stored hostname-to-IP mappings in `/etc/hosts`. Whatever is placed here is treated as the truth by that local host without verifying with other servers. However, it does not scale across hundreds of hosts."
            },
            {
                "term": "Centralized DNS & `/etc/resolv.conf`",
                "explanation": "To manage name resolution centrally, Linux systems point to DNS servers via `/etc/resolv.conf` using `nameserver <IP>` directives (e.g. `nameserver 192.168.1.100` or public DNS `nameserver 8.8.8.8`)."
            },
            {
                "term": "Resolution Priority (`/etc/nsswitch.conf`)",
                "explanation": "The Name Service Switch configuration file defines lookup precedence. The entry `hosts: files dns` tells the operating system to check `/etc/hosts` first, and if no match is found, query the DNS server."
            },
            {
                "term": "Search Domains (`search domain.com`)",
                "explanation": "Adding `search mycompany.com` to `/etc/resolv.conf` allows users to query short names like `ping web` or `ping db`; the OS automatically appends the search domain to query `web.mycompany.com`."
            },
            {
                "term": "DNS Record Types (`A`, `AAAA`, `CNAME`)",
                "explanation": "• **A Record**: Maps a hostname to an IPv4 address (e.g., `web -> 192.168.1.10`).\n• **AAAA Record**: Maps a hostname to an IPv6 address.\n• **CNAME Record**: Canonical Name alias mapping one name to another name (e.g., `eat -> hungry.mycompany.com`)."
            },
            {
                "term": "DNS Query Tools (`nslookup` vs `dig` vs `ping`)",
                "explanation": "• `ping`: Uses OS resolver (`/etc/hosts` + DNS).\n• `nslookup`: Queries the DNS server directly, ignoring `/etc/hosts`.\n• `dig`: Returns verbose DNS records, query latency, authority sections, and flags directly from nameservers."
            }
        ],
        "commands": [
            {
                "cmd": "cat /etc/hosts",
                "desc": "View local static IP-to-hostname mappings.",
                "example": "cat /etc/hosts",
                "options": "Format: `<IP> <canonical_name> [aliases]`"
            },
            {
                "cmd": "cat /etc/resolv.conf",
                "desc": "View configured DNS nameservers and search domains.",
                "example": "cat /etc/resolv.conf",
                "options": "Directives: `nameserver`, `search`, `options`"
            },
            {
                "cmd": "grep hosts /etc/nsswitch.conf",
                "desc": "Check name resolution priority order (files vs dns).",
                "example": "grep \"^hosts:\" /etc/nsswitch.conf",
                "options": "Default: `hosts: files dns`"
            },
            {
                "cmd": "nslookup <domain> [dns-server]",
                "desc": "Query internet name servers interactively or non-interactively.",
                "example": "nslookup google.com\nnslookup caleston-repos-01 192.168.1.100",
                "options": "Direct DNS server querying"
            },
            {
                "cmd": "dig <domain> [record-type]",
                "desc": "DNS lookup utility providing comprehensive record inspection and timing.",
                "example": "dig google.com\ndig @8.8.8.8 google.com +short",
                "options": "`+short` for concise output, `+trace` for full root delegation"
            },
            {
                "cmd": "host <domain>",
                "desc": "Perform simple DNS lookups.",
                "example": "host google.com",
                "options": "`-t <type>` specify query type (A, MX, CNAME)"
            }
        ],
        "exercises": [
            "Inspect your system's DNS resolver configuration: `cat /etc/resolv.conf`.",
            "Verify hostname resolution order: `grep \"^hosts:\" /etc/nsswitch.conf`.",
            "Perform a DNS query with `nslookup`: `nslookup google.com`.",
            "Perform a detailed DNS query with `dig`: `dig google.com`.",
            "Test querying a specific public nameserver: `dig @8.8.8.8 google.com +short`.",
            "Check how `/etc/hosts` functions: add a test entry `127.0.0.1 testlab.local`, run `ping -c 2 testlab.local`, then remove the line."
        ]
    },
    "0640-networking-basics": {
        "slug": "networking_basics_switching_and_routing",
        "title": "Linux Networking Basics: Interfaces, Switching, Routing & Gateways",
        "description": "Understand Linux network interfaces, local switching within subnets, inter-network routing with routers, configuring default gateways, and managing routing tables with ip and route.",
        "objectives": [
            "Identify and inspect network interfaces using `ip link` and `ip addr`.",
            "Understand Layer 2 switching for communication within the same network/subnet.",
            "Understand Layer 3 routing for connecting distinct network subnets.",
            "Understand the role of a Gateway as the exit door to external networks and the Internet.",
            "Inspect kernel routing tables using `route -n` and `ip route`.",
            "Add static routes and configure default gateways (`0.0.0.0` / `default`).",
            "Understand persistent network configuration via `/etc/network/interfaces` or Netplan."
        ],
        "key_concepts": [
            {
                "term": "Network Interfaces (`ip link` & `ip addr`)",
                "explanation": "Every network connection requires an interface (e.g., `eth0`, `enp1s0f1`, or loopback `lo`). `ip link` shows interface hardware and link states (`UP`/`DOWN`), while `ip addr` shows assigned IP addresses."
            },
            {
                "term": "Switches vs. Routers",
                "explanation": "• **Switch**: Enables communication *within* the same network (e.g., `192.168.1.0/24`). It cannot route packets across different subnets.\n• **Router**: An intelligent device with multiple ports connecting *separate* networks (e.g. `192.168.1.0` and `192.168.2.0`), assigned an IP address on each network."
            },
            {
                "term": "Gateways: The Door to Other Networks",
                "explanation": "When a host needs to communicate with an IP outside its local subnet, it cannot send directly to the host. It forwards the packet to a **Gateway** (router IP on its subnet) that knows how to route to external networks."
            },
            {
                "term": "Default Gateway (`0.0.0.0` or `default`)",
                "explanation": "Instead of defining individual routes for billions of internet addresses, systems set a **default gateway**: any packet destined for an unknown destination network is sent to this gateway."
            },
            {
                "term": "Volatile vs. Persistent Configuration",
                "explanation": "Commands like `ip addr add` or `ip route add` take effect immediately in the kernel but are lost upon reboot. To make them permanent, define them in configuration files like `/etc/network/interfaces` or `/etc/netplan/*.yaml`."
            }
        ],
        "commands": [
            {
                "cmd": "ip link show",
                "desc": "List all network interfaces and their link operational state.",
                "example": "ip link show\nip link show eth0",
                "options": "`set dev <iface> up/down` toggles link state"
            },
            {
                "cmd": "ip addr show",
                "desc": "Display IP addresses and netmasks assigned to all interfaces.",
                "example": "ip addr show\nip a",
                "options": "`-4` shows IPv4 only, `-6` shows IPv6 only"
            },
            {
                "cmd": "ip addr add <ip/mask> dev <interface>",
                "desc": "Assign an IP address to a network interface.",
                "example": "sudo ip addr add 192.168.1.50/24 dev eth0",
                "options": "Temporary until reboot"
            },
            {
                "cmd": "ip route show",
                "desc": "Display the kernel routing table.",
                "example": "ip route show\nip r",
                "options": "Replaces legacy `route -n` or `netstat -r`"
            },
            {
                "cmd": "ip route add <subnet> via <gateway>",
                "desc": "Add a static route to a destination subnet via specified router IP.",
                "example": "sudo ip route add 192.168.2.0/24 via 192.168.1.1",
                "options": "Directs traffic for subnet through router"
            },
            {
                "cmd": "ip route add default via <gateway>",
                "desc": "Set the default gateway for all external and internet traffic.",
                "example": "sudo ip route add default via 192.168.1.1",
                "options": "`default` is equivalent to destination `0.0.0.0/0`"
            }
        ],
        "exercises": [
            "Display all network interfaces and note their states: `ip link show`.",
            "Display assigned IPv4 addresses across all interfaces: `ip -4 addr show`.",
            "Inspect the current routing table: `ip route show`.",
            "Identify your machine's default gateway: `ip route | grep default`.",
            "View legacy route output: `route -n` or `netstat -rn`."
        ]
    },
    "0650-troubleshooting": {
        "slug": "network_troubleshooting",
        "title": "Network Troubleshooting: Systematic Diagnosis from Ground Up",
        "description": "Follow Jacqui's systematic troubleshooting playbook: check interface status (ip link), verify DNS lookup (nslookup), test reachability (ping), trace network hops (traceroute), and inspect listening ports (netstat/ss).",
        "objectives": [
            "Execute a systematic 5-step network troubleshooting methodology from client to server.",
            "Step 1: Verify local interface link status (`ip link`).",
            "Step 2: Test DNS name resolution to eliminate DNS misconfiguration (`nslookup` / `dig`).",
            "Step 3: Test end-to-end ICMP reachability (`ping`).",
            "Step 4: Trace router hops to isolate where along the route packets are dropped (`traceroute`).",
            "Step 5: Verify remote server health, listening ports (`netstat` / `ss`), and interface state.",
            "Bring up down interfaces using `ip link set dev <interface> up`."
        ],
        "key_concepts": [
            {
                "term": "Systematic Bottom-Up Troubleshooting",
                "explanation": "When a network service is unreachable, do not guess randomly. Troubleshoot systematically:\n1. **Local Link**: Is the network interface up? (`ip link`)\n2. **DNS Resolution**: Does the name resolve to a valid IP? (`nslookup`)\n3. **Host Reachability**: Can packets reach the host? (`ping`)\n4. **Routing Hops**: Which router hop is failing? (`traceroute`)\n5. **Service & Port**: Is the daemon listening on the target port? (`netstat` / `ss`)"
            },
            {
                "term": "Isolating Route Failures with `traceroute`",
                "explanation": "Traceroute sends packets with increasing TTL (Time-To-Live) values to discover every router hop between source and destination. If hops 1 and 2 reply but hop 3 times out with asterisks (`* * *`), the issue is isolated between router 2 and the destination server."
            },
            {
                "term": "Checking Listening Sockets (`netstat` / `ss`)",
                "explanation": "Even if the network route is perfect, a connection will timeout or be refused if no process is listening on the expected port (e.g. port 80 for HTTP). `netstat -tuln` or `ss -tuln` verifies if the application daemon is bound and listening."
            },
            {
                "term": "Fixing Down Interfaces (`ip link set dev up`)",
                "explanation": "In Jacqui and Bob's troubleshooting session, the repository server was listening on port 80, but its network interface was in the `DOWN` state. Running `ip link set dev <interface> up` brought the interface online, immediately restoring access."
            }
        ],
        "commands": [
            {
                "cmd": "ip link show",
                "desc": "Check interface state (UP/DOWN/UNKNOWN).",
                "example": "ip link show",
                "options": "Look for `<...UP...>` flag in brackets"
            },
            {
                "cmd": "nslookup <host>",
                "desc": "Verify hostname resolves to an IP address.",
                "example": "nslookup caleston-repos-01",
                "options": "Confirms DNS functionality"
            },
            {
                "cmd": "ping -c <count> <ip/host>",
                "desc": "Send echo requests and calculate packet loss percentage.",
                "example": "ping -c 3 192.168.2.5",
                "options": "100% packet loss indicates communication failure"
            },
            {
                "cmd": "traceroute <ip/host>",
                "desc": "Trace the route packets take to a network host across all gateways.",
                "example": "traceroute 192.168.2.5",
                "options": "Shows each router hop and response times"
            },
            {
                "cmd": "netstat -tuln / ss -tuln",
                "desc": "Show listening TCP and UDP sockets with numeric ports.",
                "example": "ss -tuln\nnetstat -tuln | grep \":80\"",
                "options": "`-t` TCP, `-u` UDP, `-l` listening, `-n` numeric"
            },
            {
                "cmd": "sudo ip link set dev <interface> up",
                "desc": "Enable and bring up a disabled network interface.",
                "example": "sudo ip link set dev eth0 up",
                "options": "`down` disables the interface"
            }
        ],
        "exercises": [
            "Check link state of all interfaces: `ip link show`.",
            "Verify DNS resolution of an internal or public server: `nslookup google.com`.",
            "Test ICMP echo reachability: `ping -c 4 8.8.8.8`.",
            "Run a traceroute to trace network hops: `traceroute 8.8.8.8` (or `tracepath 8.8.8.8`).",
            "Inspect all listening TCP ports on your system: `ss -tuln` (or `netstat -tuln`)."
        ]
    },
    "0438-story-section": {
        "slug": "story_section",
        "title": "Story Section: Security Incident & Access Control Escalation",
        "description": "Join Bob as security analyst Vikram flags confidential customer data exposed on a company file share, prompting urgent escalation to Andrew, and a deep-dive training session with Dave on Linux security.",
        "objectives": [
            "Understand real-world enterprise security audits and incident response procedures.",
            "Recognize risks of confidential data exposure on shared network file systems.",
            "Learn why fine-grained Linux user accounts and file permissions are critical to preventing data leaks.",
            "Prepare for core security topics: account types, access control files, chmod/chown, SSH, iptables, and cron."
        ],
        "key_concepts": [
            {
                "term": "Incident Escalation & Enterprise Audits",
                "explanation": "Routine enterprise security scans continuously monitor internal file shares for exposed sensitive data. When confidential customer records are placed on a world-readable share, security analysts (like Vikram) escalate directly to project leads."
            },
            {
                "term": "The Cost of Permissive File Permissions",
                "explanation": "Default world-readable permissions can expose proprietary intellectual property, database credentials, or customer PII. Securing files requires active permission auditing."
            },
            {
                "term": "Defense-in-Depth in Linux",
                "explanation": "Linux security relies on multiple protective layers: distinct account boundaries, restricted file permissions (chmod/chown), locked-down SSH key authentication, host firewalls (iptables), and automated log monitoring."
            }
        ],
        "commands": [
            {
                "cmd": "id",
                "desc": "Check user identity, UID, GID, and assigned groups.",
                "example": "id",
                "options": "Shows effective credentials"
            },
            {
                "cmd": "ls -ld <directory>",
                "desc": "Inspect directory permissions and ownership without listing contents.",
                "example": "ls -ld /shared/client_data",
                "options": "`-d` lists directory itself"
            },
            {
                "cmd": "who",
                "desc": "Display all users currently logged into the system.",
                "example": "who",
                "options": "Shows terminals and login timestamps"
            }
        ],
        "exercises": [
            "Run `id` to view your current user identity and group memberships.",
            "Inspect directory permissions of your personal home directory: `ls -ld ~`.",
            "Check which users are currently logged into the machine: `who`."
        ]
    },
    "0510-linux-accounts": {
        "slug": "linux_accounts_and_sudo",
        "title": "Linux Accounts, Superuser, and Sudo Privilege Escalation",
        "description": "Understand account types (root, system, service, user), UID/GID ranges, primary vs supplementary groups, switching users with su, and fine-grained administrative access via /etc/sudoers and visudo.",
        "objectives": [
            "Distinguish the four account types: Superuser (root, UID 0), System Accounts, Service Accounts, and Regular Users (UID 1000+).",
            "Inspect user accounts and group memberships using `id`, `whoami`, `who`, and `last`.",
            "Switch users and shells safely using `su` and `su -`.",
            "Configure sudo privilege escalation and granular command access via `/etc/sudoers` using `visudo`.",
            "Secure systems by disabling direct root logins using `/sbin/nologin`."
        ],
        "key_concepts": [
            {
                "term": "The 4 Linux Account Types",
                "explanation": "\u2022 **Superuser (root, UID 0)**: Unrestricted control over all files, processes, and kernel settings.\n\u2022 **System Accounts (UIDs < 100 or 500-999)**: Created during OS installation for OS processes (e.g., `sshd`, `mail`) with no interactive login.\n\u2022 **Service Accounts**: Created when server software (e.g. `nginx`, `postgres`) is installed.\n\u2022 **Regular User Accounts (UIDs 1000+)**: Created for real human users with interactive login and dedicated `/home/<user>` directories."
            },
            {
                "term": "Primary GID vs. Supplementary Groups",
                "explanation": "Every user has exactly one Primary Group (assigned upon creation, usually with the same name and GID as the user). Users can also be added to multiple Supplementary Groups (e.g., `developers`, `docker`, `wheel`) to grant group permissions across shared project resources."
            },
            {
                "term": "Switching Users: `su` vs. `sudo`",
                "explanation": "\u2022 `su <user>` switches account but requires the *target user's* password. Sharing root password compromises security.\n\u2022 `sudo <command>` allows permitted users to run administrative commands using their *own* password, with every action logged in audit trails."
            },
            {
                "term": "/etc/sudoers & Granular Delegation",
                "explanation": "Configured safely with `visudo`. Syntax: `USER HOST=(RUNAS) COMMANDS`. For example: `bob ALL=(ALL) ALL` grants full admin, while `sara ALL=(root) /sbin/shutdown` allows only system reboot. Groups are denoted with `%` (e.g. `%sudo` or `%wheel`)."
            }
        ],
        "commands": [
            {
                "cmd": "id [username]",
                "desc": "Print user identity, UID, primary GID, and supplementary groups.",
                "example": "id\nid bob",
                "options": "`-u` UID only, `-g` GID only, `-G` all groups"
            },
            {
                "cmd": "whoami",
                "desc": "Print effective username for current shell session.",
                "example": "whoami",
                "options": "Equivalent to `id -un`"
            },
            {
                "cmd": "su - <user>",
                "desc": "Switch user account with a complete login environment and user's profile.",
                "example": "su - bob",
                "options": "`-` ensures full login environment is loaded"
            },
            {
                "cmd": "sudo <command>",
                "desc": "Execute a command with superuser (root) privileges.",
                "example": "sudo systemctl restart nginx",
                "options": "`-u` <user> run as specific user instead of root"
            },
            {
                "cmd": "sudo visudo",
                "desc": "Edit `/etc/sudoers` file safely with strict syntax checking on exit.",
                "example": "sudo visudo",
                "options": "Locks file to prevent concurrent edits"
            },
            {
                "cmd": "last -n <count>",
                "desc": "View recent user login history and system reboot events.",
                "example": "last -n 10",
                "options": "Reads from `/var/log/wtmp`"
            }
        ],
        "exercises": [
            "Check your current UID, GID, and supplementary groups using `id`.",
            "Display your current logged-in username: `whoami`.",
            "Inspect recent login history: `last -n 5`.",
            "View administrative privilege definitions: `sudo cat /etc/sudoers`.",
            "Verify superuser escalation works: `sudo whoami` (should output `root`)."
        ]
    },
    "0520-user-management": {
        "slug": "user_and_group_management",
        "title": "User & Group Management (useradd, usermod, groupadd)",
        "description": "Create and administer Linux user accounts and groups: useradd with flags (-c, -d, -e, -u, -g, -G), setting passwords with passwd, deleting accounts with userdel, and managing groups with groupadd and groupdel.",
        "objectives": [
            "Create user accounts with custom properties using `useradd` flags (`-c`, `-d`, `-e`, `-u`, `-g`, `-G`, `-m`).",
            "Set, change, and manage account passwords using `passwd`.",
            "Modify existing user attributes and append secondary groups using `usermod -aG`.",
            "Delete user accounts safely with `userdel` (including `-r` to purge home directories).",
            "Create, modify, and delete Linux groups using `groupadd` and `groupdel`."
        ],
        "key_concepts": [
            {
                "term": "Creating Users (`useradd`)",
                "explanation": "Creates a new system user account. Use `-m` to generate the `/home/<username>` directory populated from `/etc/skel`. Default options can be customized with flags for UID, GID, comments, and login shell."
            },
            {
                "term": "Common `useradd` Flags",
                "explanation": "\u2022 `-c <text>`: GECOS field (full name/comment).\n\u2022 `-d <path>`: Custom home directory location.\n\u2022 `-e <YYYY-MM-DD>`: Account expiration date.\n\u2022 `-u <UID>`: Specify custom user ID.\n\u2022 `-g <GID/name>`: Set primary group.\n\u2022 `-G <group1,group2>`: Set supplementary groups.\n\u2022 `-s <shell>`: Assign login shell (e.g., `/bin/bash` or `/sbin/nologin`)."
            },
            {
                "term": "Modifying Groups with `usermod -aG`",
                "explanation": "CRITICAL RULE: When adding a user to a supplementary group, always use `-a` (append) together with `-G` (`sudo usermod -aG docker bob`). Omitting `-a` will remove the user from all other secondary groups they previously belonged to!"
            },
            {
                "term": "Managing Groups (`groupadd` & `groupdel`)",
                "explanation": "`groupadd <groupname>` creates a new group. `groupdel <groupname>` removes a group. Group details and members are stored in `/etc/group`."
            }
        ],
        "commands": [
            {
                "cmd": "sudo useradd -m -s /bin/bash <user>",
                "desc": "Create a new user with home directory and bash login shell.",
                "example": "sudo useradd -m -s /bin/bash bob",
                "options": "`-m` creates home directory"
            },
            {
                "cmd": "sudo passwd <user>",
                "desc": "Set or update password for a user account.",
                "example": "sudo passwd bob",
                "options": "`-l` locks account, `-u` unlocks"
            },
            {
                "cmd": "sudo usermod -aG <group> <user>",
                "desc": "Append a user to a supplementary group without removing existing groups.",
                "example": "sudo usermod -aG developers bob",
                "options": "Always use `-a` with `-G`"
            },
            {
                "cmd": "sudo userdel -r <user>",
                "desc": "Delete a user account and remove their home directory and mail spool.",
                "example": "sudo userdel -r bob",
                "options": "`-r` purges user files"
            },
            {
                "cmd": "sudo groupadd [-g GID] <group>",
                "desc": "Create a new system group with optional custom GID.",
                "example": "sudo groupadd -g 2001 developers",
                "options": "`-g` custom GID"
            },
            {
                "cmd": "sudo groupdel <group>",
                "desc": "Delete an existing group.",
                "example": "sudo groupdel developers",
                "options": "Cannot delete primary group of existing user"
            }
        ],
        "exercises": [
            "Create a test developer group: `sudo groupadd testdevs`.",
            "Create a new user assigned to the group: `sudo useradd -m -c \"Dev Account\" -G testdevs devbob`.",
            "Verify group memberships: `id devbob`.",
            "Set a password for the new user: `sudo passwd devbob`.",
            "Clean up: `sudo userdel -r devbob && sudo groupdel testdevs`."
        ]
    },
    "0530-access-control-files": {
        "slug": "access_control_files",
        "title": "Access Control Files: Deep Dive into /etc/passwd, /etc/shadow, and /etc/group",
        "description": "Examine the internal structure and field-by-field layout of Linux identity files: the 7 fields of /etc/passwd, hashed passwords and expiration policies in /etc/shadow, and group memberships in /etc/group.",
        "objectives": [
            "Inspect and parse all 7 colon-separated fields in `/etc/passwd`.",
            "Understand why passwords are removed from `/etc/passwd` (`x`) and stored in `/etc/shadow`.",
            "Parse the 9 fields of `/etc/shadow` including password hashing algorithms, epoch days, and aging policies.",
            "Parse the 4 fields of `/etc/group` and verify group memberships.",
            "Understand why access control files must never be edited directly with standard text editors."
        ],
        "key_concepts": [
            {
                "term": "Anatomy of `/etc/passwd` (7 Fields)",
                "explanation": "Colon-separated fields:\n1. **Username**: Login identifier.\n2. **Password (`x`)**: Masked pointer indicating password hash is in `/etc/shadow`.\n3. **UID**: Numeric user ID.\n4. **GID**: Numeric primary group ID.\n5. **GECOS**: Comment / User's real name.\n6. **Home Directory**: Absolute path (e.g. `/home/bob`).\n7. **Shell**: Path to login binary (e.g. `/bin/bash` or `/sbin/nologin`).\nWorld-readable permissions (`644`)."
            },
            {
                "term": "Anatomy of `/etc/shadow` (9 Fields)",
                "explanation": "Restricted permissions (`600` or `640`, root-only):\n1. **Username**\n2. **Hashed Password**: Salted SHA-512 hash (`$6$...`). Asterisk `*` or `!` means locked / no password.\n3. **Last Changed**: Days since Unix epoch (Jan 1, 1970).\n4. **Minimum Days**: Wait time before password can be changed again.\n5. **Maximum Days**: Validity period before password must be changed.\n6. **Warning Days**: Days in advance user is warned of expiration.\n7. **Inactive Days**: Days after expiry before account is disabled.\n8. **Account Expiration**: Absolute expiry date in epoch days.\n9. **Reserved**"
            },
            {
                "term": "Anatomy of `/etc/group` (4 Fields)",
                "explanation": "1. **Group Name**\n2. **Group Password (`x`)**\n3. **GID**: Numeric group ID.\n4. **Member List**: Comma-separated usernames."
            },
            {
                "term": "Safe Editing Utilities (`vipw`, `vigr`)",
                "explanation": "Direct editing of `/etc/passwd` or `/etc/shadow` in standard text editors can corrupt account tables or lose edits during concurrent logins. Utilities like `vipw` and `vigr` use file locking to prevent corruption."
            }
        ],
        "commands": [
            {
                "cmd": "getent passwd <user>",
                "desc": "Query user entry from passwd file or network directory services.",
                "example": "getent passwd bob",
                "options": "Resolves through NSSwitch"
            },
            {
                "cmd": "getent group <group>",
                "desc": "Query group entry and member list.",
                "example": "getent group sudo",
                "options": "Works for local and LDAP groups"
            },
            {
                "cmd": "sudo chage -l <user>",
                "desc": "Display comprehensive password aging and expiration dates.",
                "example": "sudo chage -l bob",
                "options": "Shows last change, expiry, and warning days"
            },
            {
                "cmd": "sudo vipw",
                "desc": "Safely edit `/etc/passwd` with atomic file locking.",
                "example": "sudo vipw",
                "options": "`-s` edits `/etc/shadow` safely"
            }
        ],
        "exercises": [
            "Inspect your user account entry: `grep \"^$USER:\" /etc/passwd`.",
            "Parse each field of your entry by matching against the 7-field structure.",
            "Inspect your primary group entry: `grep \"^$USER:\" /etc/group`.",
            "Check password aging policies for your account: `sudo chage -l $USER`."
        ]
    },
    "0550-file-permissions-and-ownership": {
        "slug": "file_permissions_and_ownership",
        "title": "Linux File Permissions & Ownership (chmod, chown, chgrp)",
        "description": "Master the Linux security model: read/write/execute permissions for user, group, and others; directory permission semantics; symbolic vs. numeric (octal) chmod; and changing owners and groups with chown and chgrp.",
        "objectives": [
            "Read and interpret the 10-character `ls -l` permission string.",
            "Understand permission triplets: User/Owner (`u`), Group (`g`), and Others (`o`).",
            "Differentiate file vs directory permissions (specifically execute `x` on directories allowing `cd`).",
            "Understand sequential permission evaluation (owner check -> group check -> others).",
            "Calculate octal permission values (Read = 4, Write = 2, Execute = 1).",
            "Apply permissions using `chmod` in both symbolic (`u+x`, `g-w`, `o=r`) and octal (`755`, `644`, `700`) modes.",
            "Change file and directory owners and groups using `chown` and `chgrp`."
        ],
        "key_concepts": [
            {
                "term": "Anatomy of the 10-Character Permission String",
                "explanation": "\u2022 **Position 1**: File type (`-` regular file, `d` directory, `l` symbolic link, `c` character device, `b` block device, `s` socket, `p` pipe).\n\u2022 **Positions 2-4**: Owner permissions (`u`)\n\u2022 **Positions 5-7**: Group permissions (`g`)\n\u2022 **Positions 8-10**: Others permissions (`o`)"
            },
            {
                "term": "Octal Numeric Values",
                "explanation": "\u2022 **Read (`r`)** = 4\n\u2022 **Write (`w`)** = 2\n\u2022 **Execute (`x`)** = 1\n\u2022 **No Permission (`-`)** = 0\nSumming values yields octal digits: `rwx` = 7 (4+2+1), `rw-` = 6 (4+2), `r-x` = 5 (4+1), `r--` = 4, `---` = 0."
            },
            {
                "term": "Directory Permission Semantics",
                "explanation": "\u2022 **Read (`r`)**: Can list file names inside directory (`ls`).\n\u2022 **Write (`w`)**: Can create, delete, and rename files inside directory.\n\u2022 **Execute (`x`)**: Can enter directory (`cd`) and access metadata of files inside. Without `x`, read or write on files inside is blocked!"
            },
            {
                "term": "Sequential Permission Evaluation",
                "explanation": "Linux checks identity in strict order: (1) If you are the owner, ONLY the owner's permissions apply. (2) If not owner but member of group, ONLY group permissions apply. (3) Otherwise, others permissions apply. Group permissions are NEVER evaluated for the owner, even if group has more access!"
            }
        ],
        "commands": [
            {
                "cmd": "chmod <mode> <file>",
                "desc": "Change file access permissions using octal or symbolic modes.",
                "example": "chmod 755 script.sh\nchmod u+x,g-w script.sh",
                "options": "`-R` recursive for directories"
            },
            {
                "cmd": "chmod -R <mode> <dir>",
                "desc": "Change permissions recursively throughout an entire directory tree.",
                "example": "chmod -R 750 /opt/project",
                "options": "Modifies parent and all children"
            },
            {
                "cmd": "chown <user>[:<group>] <path>",
                "desc": "Change the owner user and optional owner group of files or directories.",
                "example": "sudo chown bob:developers app.py\nsudo chown -R bob /opt/myapp",
                "options": "`-R` recursive"
            },
            {
                "cmd": "chgrp <group> <path>",
                "desc": "Change group ownership of files or directories.",
                "example": "sudo chgrp developers app.py",
                "options": "`-R` recursive"
            },
            {
                "cmd": "umask",
                "desc": "View or set the default permission mask applied to newly created files/directories.",
                "example": "umask\numask 027",
                "options": "Default file perms = 666 - umask; dir perms = 777 - umask"
            }
        ],
        "exercises": [
            "Create a test file: `touch test_perms.txt` and check its default permissions: `ls -l test_perms.txt`.",
            "Make it read-write only for owner (octal 600): `chmod 600 test_perms.txt && ls -l test_perms.txt`.",
            "Add execute permission symbolically: `chmod u+x test_perms.txt && ls -l test_perms.txt`.",
            "Create a test script, make it executable with 755, and run it: `echo 'echo Hello' > run.sh && chmod 755 run.sh && ./run.sh`.",
            "Clean up: `rm test_perms.txt run.sh`."
        ]
    },
    "0570-ssh-and-scp": {
        "slug": "ssh_and_scp",
        "title": "Remote Server Access & Transfer: SSH, Key-Based Authentication, and SCP",
        "description": "Connect securely to remote Linux servers using SSH on port 22, generate public/private key pairs with ssh-keygen, configure password-less authentication with ssh-copy-id, and transfer files remotely with scp.",
        "objectives": [
            "Understand the client-server architecture of SSH (port 22) and secure remote terminals.",
            "Connect to remote Linux servers using `ssh [user@]host`.",
            "Generate asymmetric cryptographic key pairs (private key `id_rsa` and public key `id_rsa.pub`) with `ssh-keygen`.",
            "Deploy public keys to remote servers using `ssh-copy-id` into `~/.ssh/authorized_keys`.",
            "Transfer files securely over SSH using `scp`.",
            "Use recursive (`-r`) and attribute preservation (`-p`) flags with `scp`."
        ],
        "key_concepts": [
            {
                "term": "SSH Architecture (Port 22)",
                "explanation": "Secure Shell replaces legacy unencrypted protocols (telnet, rsh). The SSH daemon (`sshd`) runs on port 22 on servers. Clients initiate encrypted sessions carrying remote shells, commands, or data streams."
            },
            {
                "term": "Asymmetric Cryptography: Private vs. Public Keys",
                "explanation": "\u2022 **Private Key (`~/.ssh/id_rsa`)**: Kept strictly confidential on client machine; must have permissions `600` (`-rw-------`). Never shared with anyone!\n\u2022 **Public Key (`~/.ssh/id_rsa.pub`)**: Can be freely shared and distributed. Copied to remote servers to unlock logins."
            },
            {
                "term": "Password-less Login & `authorized_keys`",
                "explanation": "When an SSH client connects, `sshd` challenges the client with a cryptographic challenge solved only by the matching private key. Once verified against `~/.ssh/authorized_keys`, login completes instantly without typing passwords."
            },
            {
                "term": "Secure Copy Protocol (`scp`)",
                "explanation": "SCP transfers files securely over SSH channels. Syntax: `scp [options] [user@]source:[path] [user@]destination:[path]`. Preserves network security using SSH authentication."
            }
        ],
        "commands": [
            {
                "cmd": "ssh [user@]<host>",
                "desc": "Initiate an encrypted remote terminal shell session.",
                "example": "ssh bob@devapp01\nssh 172.16.238.10",
                "options": "`-p <port>` custom port, `-i <key>` specify private key"
            },
            {
                "cmd": "ssh-keygen -t rsa -b 4096",
                "desc": "Generate asymmetric RSA key pair with specified bit length.",
                "example": "ssh-keygen -t rsa -b 4096",
                "options": "`-f <file>` specify output file, `-N \"\"` for empty passphrase"
            },
            {
                "cmd": "ssh-copy-id [user@]<host>",
                "desc": "Copy client public key into remote server's `~/.ssh/authorized_keys`.",
                "example": "ssh-copy-id bob@devapp01",
                "options": "Automates remote key setup"
            },
            {
                "cmd": "scp <source> <dest>",
                "desc": "Copy files securely across network hosts using SSH.",
                "example": "scp app.tar.gz bob@devapp01:~/",
                "options": "`-r` recursive directory copy, `-p` preserve timestamps and permissions"
            }
        ],
        "exercises": [
            "Check for existing SSH keys on your machine: `ls -la ~/.ssh`.",
            "Generate a test key pair: `ssh-keygen -t rsa -b 2048 -f /tmp/test_ssh_key -N \"\"`.",
            "Verify file permissions: `ls -l /tmp/test_ssh_key*` (notice private key is 600).",
            "View public key format: `cat /tmp/test_ssh_key.pub`.",
            "Clean up: `rm /tmp/test_ssh_key*`."
        ]
    },
    "0585-ip-tables": {
        "slug": "iptables_firewall_fundamentals",
        "title": "Network Security Fundamentals: Linux IPtables Architecture & Chains",
        "description": "Understand host-based firewall architecture in Linux: packet filtering with Netfilter, default policies, chains (INPUT, OUTPUT, FORWARD), rule evaluation order, and matching packets by source, destination, port, and protocol.",
        "objectives": [
            "Understand host-based firewalls vs. hardware perimeter network appliances.",
            "Differentiate the three default Netfilter chains: `INPUT`, `OUTPUT`, and `FORWARD`.",
            "Understand chain default policies (`ACCEPT` vs `DROP`).",
            "Learn top-to-bottom rule evaluation and first-match execution semantics.",
            "Understand filtering criteria: source IP (`-s`), destination IP (`-d`), protocol (`-p`), and port (`--dport`).",
            "Inspect existing firewall tables and rules with `iptables -L`."
        ],
        "key_concepts": [
            {
                "term": "Host Firewalls vs Perimeter Firewalls",
                "explanation": "Perimeter appliances (Cisco ASA, Fortinet) guard the network boundary. Host-level firewalls (IPtables, FirewallD) protect the individual Linux host from internal lateral movements, rogue dev servers, or unauthorized service access."
            },
            {
                "term": "The 3 Core Chains in Filter Table",
                "explanation": "\u2022 **INPUT**: Traversed by network packets arriving at the host addressed to local processes.\n\u2022 **OUTPUT**: Traversed by network packets created locally by host processes heading outside.\n\u2022 **FORWARD**: Traversed by packets passing through this machine to another destination (routing)."
            },
            {
                "term": "Top-to-Bottom First-Match Semantics",
                "explanation": "Rules inside a chain are evaluated in strict sequence from top to bottom. The first rule that matches packet criteria triggers the target action (`ACCEPT`, `DROP`, `REJECT`), and evaluation terminates immediately! If no rule matches, the chain's default policy is applied."
            },
            {
                "term": "Filtering Parameters",
                "explanation": "Rules match packets based on:\n\u2022 `-p <protocol>`: `tcp`, `udp`, `icmp`.\n\u2022 `-s <source>`: IP or CIDR range (e.g. `172.16.238.187`).\n\u2022 `-d <destination>`: Target IP or network.\n\u2022 `--dport <port>`: Destination service port (e.g. `22`, `80`, `5432`).\n\u2022 `-j <target>`: `ACCEPT`, `DROP` (silent discard), or `REJECT` (ICMP unreachable)."
            }
        ],
        "commands": [
            {
                "cmd": "sudo iptables -L",
                "desc": "List all active rules across default chains in filter table.",
                "example": "sudo iptables -L",
                "options": "Shows INPUT, FORWARD, and OUTPUT chains"
            },
            {
                "cmd": "sudo iptables -L -n -v",
                "desc": "List rules with numeric IP addresses/ports and packet/byte traffic counters.",
                "example": "sudo iptables -L -n -v",
                "options": "`-n` numeric (faster, no DNS delays), `-v` verbose"
            },
            {
                "cmd": "sudo iptables -L --line-numbers",
                "desc": "Display rules with line numbers for precise insertion and deletion.",
                "example": "sudo iptables -L INPUT --line-numbers",
                "options": "Indicates rule index in chain"
            },
            {
                "cmd": "sudo iptables -P <chain> <ACCEPT/DROP>",
                "desc": "Change default chain policy.",
                "example": "sudo iptables -P FORWARD DROP",
                "options": "Default policy when no rules match"
            },
            {
                "cmd": "sudo iptables -F",
                "desc": "Flush (wipe) all rules from current table (Caution: can sever SSH connection!).",
                "example": "sudo iptables -F",
                "options": "Clears all rules"
            }
        ],
        "exercises": [
            "Check if iptables is installed and available: `which iptables`.",
            "Display current rules with numeric addresses: `sudo iptables -L -n -v`.",
            "Display current rules with line numbers: `sudo iptables -L --line-numbers`.",
            "Inspect default chain policies: `sudo iptables -S`."
        ]
    },
    "0586-securing-the-dev-environment": {
        "slug": "securing_dev_environment_iptables",
        "title": "Securing Environments with IPtables: Appending, Inserting, and Rule Precedence",
        "description": "Implement practical firewall security: append filtering rules (-A), insert high-priority overrides (-I), reject unauthorized traffic, isolate database ports, and inspect connections with netstat.",
        "objectives": [
            "Construct specific filtering rules using `-A` (append) and `-I` (insert).",
            "Allow inbound traffic for authorized clients while dropping unauthorized attempts.",
            "Isolate database ports (e.g., PostgreSQL port 5432) so only the application server can connect.",
            "Control outbound traffic (block direct Internet access while permitting internal repository updates).",
            "Insert rules with line numbers to override broad drop rules (`iptables -I OUTPUT 1 ...`).",
            "Delete rules cleanly by line number using `iptables -D <chain> <num>`.",
            "Understand stateful returning traffic on client ephemeral ports (32768\u201360999)."
        ],
        "key_concepts": [
            {
                "term": "Appending (`-A`) vs. Inserting (`-I`)",
                "explanation": "\u2022 `-A <chain>`: Appends the rule to the end of the chain.\n\u2022 `-I <chain> [index]`: Inserts the rule at specified position (default: 1, top of chain). Essential when overriding a catch-all drop rule situated at the end of the chain."
            },
            {
                "term": "DROP vs. REJECT",
                "explanation": "\u2022 `DROP`: Silently ignores the packet without sending any acknowledgment. Client waits until connection timeout.\n\u2022 `REJECT`: Drops the packet and sends an ICMP port unreachable message immediately to the client, providing faster feedback."
            },
            {
                "term": "Database Isolation (PostgreSQL 5432)",
                "explanation": "Database tiers should never accept connections from arbitrary servers. On the DB server: (1) `iptables -A INPUT -p tcp -s 172.16.238.10 --dport 5432 -j ACCEPT` allows the app server. (2) `iptables -A INPUT -p tcp --dport 5432 -j REJECT` blocks all other servers."
            },
            {
                "term": "Returning Traffic & Ephemeral Ports",
                "explanation": "When an application establishes an outbound connection to port 5432, the local kernel assigns a temporary random port (ephemeral port, typically 32768-60999). Returning packets from the database arrive on this ephemeral port, requiring matching ingress rules or established state tracking."
            }
        ],
        "commands": [
            {
                "cmd": "sudo iptables -A INPUT -p tcp -s <ip> --dport 22 -j ACCEPT",
                "desc": "Permit SSH connections from a specific client IP address.",
                "example": "sudo iptables -A INPUT -p tcp -s 172.16.238.187 --dport 22 -j ACCEPT",
                "options": "Appends rule to INPUT chain"
            },
            {
                "cmd": "sudo iptables -A INPUT -p tcp --dport 22 -j REJECT",
                "desc": "Reject SSH connections from all other source addresses.",
                "example": "sudo iptables -A INPUT -p tcp --dport 22 -j REJECT",
                "options": "Placed after allow rules"
            },
            {
                "cmd": "sudo iptables -I OUTPUT 1 -p tcp -d <ip> --dport 443 -j ACCEPT",
                "desc": "Insert a high-priority outbound allow rule at position 1.",
                "example": "sudo iptables -I OUTPUT 1 -p tcp -d 172.16.238.200 --dport 443 -j ACCEPT",
                "options": "Overrides later drop rules"
            },
            {
                "cmd": "sudo iptables -D OUTPUT <num>",
                "desc": "Delete a rule by its chain line number.",
                "example": "sudo iptables -D OUTPUT 5",
                "options": "Removes rule at position 5"
            },
            {
                "cmd": "netstat -tuln / ss -tuln",
                "desc": "Inspect listening service ports before applying firewall rules.",
                "example": "ss -tuln | grep \":5432\"",
                "options": "Shows active listening sockets"
            }
        ],
        "exercises": [
            "List existing INPUT rules with line numbers: `sudo iptables -L INPUT -n --line-numbers`.",
            "Add a test loopback allow rule: `sudo iptables -A INPUT -i lo -j ACCEPT`.",
            "Verify rule addition: `sudo iptables -L INPUT -n --line-numbers`.",
            "Delete the test rule by line number: `sudo iptables -D INPUT 1` (or matching index)."
        ]
    },
    "0595-cronjobs": {
        "slug": "cron_jobs_and_scheduling",
        "title": "Task Automation & Scheduling with Cron Jobs",
        "description": "Automate repetitive system administration tasks with cron: the background crond daemon, crontab management (-e, -l, -r), the 5-field time specification syntax (minute, hour, dom, month, dow), and syslog auditing.",
        "objectives": [
            "Understand the cron architecture and the background scheduling daemon (`crond` / `cron`).",
            "Manage user crontabs using `crontab -e` (edit), `crontab -l` (list), and `crontab -r` (remove).",
            "Master the 5-field crontab time format: `Minute Hour Day-of-Month Month Day-of-Week`.",
            "Use time operators: `*` (every), `,` (list), `-` (range), and `*/n` (step intervals).",
            "Direct output and errors from cron jobs to log files (`>> /var/log/myjob.log 2>&1`).",
            "Audit and verify cron job executions in `/var/log/syslog` or `/var/log/cron`."
        ],
        "key_concepts": [
            {
                "term": "The Cron Daemon (`crond`)",
                "explanation": "A background service that wakes up once every minute, reads user crontabs in `/var/spool/cron/crontabs` and system crontabs in `/etc/crontab`, and executes commands whose schedules match the current minute."
            },
            {
                "term": "The 5-Field Schedule Syntax",
                "explanation": "```\n*     *     *     *     *     command\n\u252c     \u252c     \u252c     \u252c     \u252c\n\u2502     \u2502     \u2502     \u2502     \u2514\u2500\u2500 Day of Week (0-7, 0 or 7 = Sunday)\n\u2502     \u2502     \u2502     \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 Month (1-12)\n\u2502     \u2502     \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 Day of Month (1-31)\n\u2502     \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 Hour (0-23)\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 Minute (0-59)\n```"
            },
            {
                "term": "Schedule Operators",
                "explanation": "\u2022 `*`: Any / every value.\n\u2022 `*/n`: Step interval (e.g. `*/5 * * * *` = every 5 minutes).\n\u2022 `,`: Comma-separated list (e.g. `1,15,30` = 1st, 15th, and 30th minutes).\n\u2022 `-`: Range of values (e.g. `1-5` in day-of-week = Monday through Friday)."
            },
            {
                "term": "Environment & Logging Pitfalls",
                "explanation": "Cron runs in a minimal environment without a terminal. (1) Always use absolute paths for executables (e.g. `/usr/bin/uptime`, `/usr/bin/python3`). (2) Always redirect standard output and standard error: `>> /path/to/log.txt 2>&1`."
            }
        ],
        "commands": [
            {
                "cmd": "crontab -e",
                "desc": "Edit current user's crontab schedule in text editor.",
                "example": "crontab -e",
                "options": "Opens editor defined by $EDITOR"
            },
            {
                "cmd": "crontab -l",
                "desc": "List current user's scheduled cron tasks.",
                "example": "crontab -l",
                "options": "Outputs crontab file to terminal"
            },
            {
                "cmd": "crontab -r",
                "desc": "Remove (delete) all crontab jobs for current user.",
                "example": "crontab -r",
                "options": "Caution: deletes entire personal crontab"
            },
            {
                "cmd": "sudo crontab -u <user> -l",
                "desc": "List another user's crontab as root administrator.",
                "example": "sudo crontab -u bob -l",
                "options": "`-u` specifies user"
            },
            {
                "cmd": "grep CRON /var/log/syslog",
                "desc": "Audit cron execution logs and timestamps in system logs.",
                "example": "grep CRON /var/log/syslog | tail -n 10",
                "options": "On RHEL/CentOS check `/var/log/cron`"
            }
        ],
        "exercises": [
            "Display your current user's scheduled jobs: `crontab -l`.",
            "Schedule a test task that writes the date every 5 minutes: `(crontab -l 2>/dev/null; echo \"*/5 * * * * /usr/bin/date >> /tmp/cron_test.log 2>&1\") | crontab -`.",
            "Verify the scheduled task: `crontab -l`.",
            "Clean up: `crontab -r`."
        ]
    },
    "0810-story-section": {
        "slug": "story_section",
        "title": "Story Section: Persistent Services & Background Daemons",
        "description": "Join Bob two days before the demo as his Django application keeps stopping whenever he closes his terminal or reboots his laptop, leading Dave to introduce systemd background services and Ansible automation.",
        "objectives": [
            "Understand the limitations of launching services directly from interactive shell sessions.",
            "Recognize the necessity of daemonization and process management in production systems.",
            "Learn the role of systemd as the Linux service manager and init system.",
            "Prepare for creating systemd service units, defining dependencies, and managing auto-restart policies."
        ],
        "key_concepts": [
            {
                "term": "Interactive Terminals vs. Background Daemons",
                "explanation": "Processes started in interactive terminal sessions receive a SIGHUP (hangup signal) when the session terminates or SSH disconnects, killing the application. Daemons decouple from terminals, manage their own life cycles, and survive reboots."
            },
            {
                "term": "The Role of Systemd as PID 1",
                "explanation": "Systemd acts as the master init process (PID 1), orchestrating system startup, tracking processes in control groups (cgroups), managing inter-service dependencies, and auto-restarting crashed services."
            },
            {
                "term": "Infrastructure Automation (Ansible)",
                "explanation": "In large enterprise environments, Dave explains that server configuration, patching, and service deployment across hundreds of hosts are automated consistently using configuration management tools like Ansible."
            }
        ],
        "commands": [
            {
                "cmd": "ps aux | grep <process>",
                "desc": "View running processes and identify background daemons.",
                "example": "ps aux | grep python",
                "options": "Shows PID, CPU/memory usage, and process state"
            },
            {
                "cmd": "nohup <command> &",
                "desc": "Legacy technique to run a command immune to hangups in background.",
                "example": "nohup python3 app.py &",
                "options": "Redirects output to nohup.out"
            },
            {
                "cmd": "systemctl --version",
                "desc": "Check installed systemd version and system features.",
                "example": "systemctl --version",
                "options": "Shows compiled features and architecture"
            }
        ],
        "exercises": [
            "Check if systemd is running as PID 1 on your Linux system: `ps -p 1 -o comm=`.",
            "Inspect active services running in the background: `systemctl list-units --type=service --state=running`.",
            "Test running a detached background process: `sleep 100 &` and view its PID with `jobs -l`."
        ]
    },
    "0830-creating-a-systemd-service": {
        "slug": "creating_systemd_service",
        "title": "Creating Systemd Services: Unit, Service & Install Configurations",
        "description": "Author production-grade systemd service unit files from scratch: configure [Unit] dependencies (After=), [Service] execution (ExecStart=, User=, Restart=on-failure, RestartSec=), and [Install] boot targets (WantedBy=).",
        "objectives": [
            "Create custom systemd service unit files located under `/etc/systemd/system/`.",
            "Configure the `[Unit]` section with metadata (`Description=`) and ordering dependencies (`After=`).",
            "Configure the `[Service]` section with `ExecStart=`, custom unprivileged service accounts (`User=`), and fault-tolerant restarts (`Restart=on-failure`, `RestartSec=10`).",
            "Configure the `[Install]` section with boot targets (`WantedBy=graphical.target` or `multi-user.target`).",
            "Reload the systemd manager configuration using `systemctl daemon-reload`.",
            "Enable services to automatically launch on system boot."
        ],
        "key_concepts": [
            {
                "term": "Unit File Location Hierarchy",
                "explanation": "Custom administrator-created unit files belong in `/etc/systemd/system/` (takes highest precedence). Packaged distribution units reside in `/lib/systemd/system/` or `/usr/lib/systemd/system/`."
            },
            {
                "term": "Three Core Unit Sections",
                "explanation": "\u2022 **[Unit]**: General metadata (`Description=`, `Documentation=`) and ordering/dependency constraints (e.g. `After=postgresql.service` ensures database is ready before the application starts).\n\u2022 **[Service]**: Defines how the service runs: `ExecStart=` (absolute binary path), `User=` (runs as unprivileged service account), `Restart=on-failure` (recovers from unexpected crashes), and `RestartSec=10` (cooldown delay before retry).\n\u2022 **[Install]**: Defines enabling behavior (`WantedBy=multi-user.target` or `WantedBy=graphical.target`), creating symlinks upon `systemctl enable`."
            },
            {
                "term": "Reloading the Daemon (`daemon-reload`)",
                "explanation": "Whenever a unit file on disk is created or edited, systemd must be notified via `systemctl daemon-reload` to re-parse the configuration and regenerate internal dependency graphs before starting or restarting."
            }
        ],
        "commands": [
            {
                "cmd": "sudo systemctl daemon-reload",
                "desc": "Reload systemd manager configuration and re-read all unit files from disk.",
                "example": "sudo systemctl daemon-reload",
                "options": "Mandatory after modifying unit files"
            },
            {
                "cmd": "sudo systemctl start <service>",
                "desc": "Start a service unit immediately.",
                "example": "sudo systemctl start project-mercury.service",
                "options": "Activates the unit"
            },
            {
                "cmd": "sudo systemctl stop <service>",
                "desc": "Stop a running service unit.",
                "example": "sudo systemctl stop project-mercury.service",
                "options": "Deactivates the unit"
            },
            {
                "cmd": "sudo systemctl enable <service>",
                "desc": "Configure service to start automatically during system boot.",
                "example": "sudo systemctl enable project-mercury.service",
                "options": "Creates WantedBy symlink in target directory"
            },
            {
                "cmd": "sudo systemctl disable <service>",
                "desc": "Prevent service from starting automatically during system boot.",
                "example": "sudo systemctl disable project-mercury.service",
                "options": "Removes target symlink"
            },
            {
                "cmd": "systemctl status <service>",
                "desc": "Display current operational status, main PID, memory, and recent log messages.",
                "example": "systemctl status project-mercury.service",
                "options": "Shows active (running), inactive, or failed"
            }
        ],
        "exercises": [
            "Inspect an existing standard system service unit: `cat /lib/systemd/system/cron.service` (or `ssh.service`).",
            "Identify the [Unit], [Service], and [Install] sections in the file.",
            "Verify whether the service is enabled for boot: `systemctl is-enabled cron`.",
            "Practice testing daemon reload: `sudo systemctl daemon-reload`."
        ]
    },
    "0840-systemd-tools": {
        "slug": "systemd_tools_and_journalctl",
        "title": "Systemd Management Tools: systemctl, journalctl & Service Debugging",
        "description": "Master service lifecycle administration with systemctl (start, stop, restart, reload, status, edit --full), inspect system targets, query central logs with journalctl (-u, -b, -f), and debug service failures.",
        "objectives": [
            "Control service lifecycles using `systemctl` (`start`, `stop`, `restart`, `reload`, `status`).",
            "Identify unit operational states: `active (running)`, `inactive (dead)`, `failed`, `activating`, and `deactivating`.",
            "Edit unit definitions on the fly using `systemctl edit --full`.",
            "Query and manage systemd runlevel targets (`systemctl get-default`, `set-default`).",
            "Filter and inspect binary system logs using `journalctl` (by unit `-u`, current boot `-b`, and live tailing `-f`).",
            "Diagnose root causes of crashed services and misconfigured daemon dependencies."
        ],
        "key_concepts": [
            {
                "term": "Restart vs. Reload",
                "explanation": "\u2022 **restart**: Completely stops the running process and starts a fresh one. Causes a momentary disruption.\n\u2022 **reload**: Sends a reload signal (typically SIGHUP) asking the application daemon to re-read its configuration files without dropping existing network connections."
            },
            {
                "term": "Unit States",
                "explanation": "\u2022 `active (running)`: Service is executing normally.\n\u2022 `inactive (dead)`: Service is stopped cleanly.\n\u2022 `failed`: Service exited with a non-zero exit code or crashed.\n\u2022 `activating` / `deactivating`: Transient states during initialization or shutdown."
            },
            {
                "term": "Safe Editing with `systemctl edit --full`",
                "explanation": "Opens unit in system editor, writes to `/etc/systemd/system/`, and reloads daemon automatically upon save without needing manual `daemon-reload`."
            },
            {
                "term": "Centralized Logging with `journalctl`",
                "explanation": "Systemd captures stdout and stderr from all managed services into a high-performance indexed binary journal (`systemd-journald`). Filters include:\n\u2022 `-u <unit>`: Filter events for that specific service.\n\u2022 `-b`: Filter events occurring since the latest boot.\n\u2022 `-f`: Live tailing (like `tail -f`).\n\u2022 `-n <count>`: Limit output to last N lines."
            }
        ],
        "commands": [
            {
                "cmd": "systemctl status <service>",
                "desc": "Show comprehensive status, main PID, memory, and recent journal log entries.",
                "example": "systemctl status ssh",
                "options": "Shows active status and recent log lines"
            },
            {
                "cmd": "sudo systemctl restart <service>",
                "desc": "Stop and start service process immediately.",
                "example": "sudo systemctl restart nginx",
                "options": "Refreshes all processes"
            },
            {
                "cmd": "sudo systemctl reload <service>",
                "desc": "Reload service configuration files without dropping active connections.",
                "example": "sudo systemctl reload nginx",
                "options": "Graceful re-configuration"
            },
            {
                "cmd": "sudo systemctl edit --full <service>",
                "desc": "Open and edit unit definition in text editor, auto-reloading daemon on save.",
                "example": "sudo systemctl edit --full project-mercury.service",
                "options": "Creates override or custom copy"
            },
            {
                "cmd": "systemctl list-units --type=service",
                "desc": "List all currently loaded and active service units.",
                "example": "systemctl list-units --type=service --state=running",
                "options": "Add `--all` to include inactive and failed units"
            },
            {
                "cmd": "journalctl -u <service> -n 50",
                "desc": "View the last 50 log entries produced by a specific service unit.",
                "example": "journalctl -u cron -n 50",
                "options": "`-u` unit name, `-n` line count"
            },
            {
                "cmd": "journalctl -u <service> -f",
                "desc": "Follow live streaming log output from a service unit in real time.",
                "example": "journalctl -u nginx -f",
                "options": "`-f` follow mode (Ctrl+C to quit)"
            },
            {
                "cmd": "journalctl -b",
                "desc": "View all system logs recorded since the current boot.",
                "example": "journalctl -b -p err",
                "options": "`-p err` filters by priority error and above"
            }
        ],
        "exercises": [
            "Check status of your system's cron service: `systemctl status cron` (or `systemd-journald`).",
            "View all currently running services: `systemctl list-units --type=service --state=running`.",
            "Inspect your system's default boot target: `systemctl get-default`.",
            "Query the last 20 log entries of systemd-journald: `journalctl -u systemd-journald -n 20`.",
            "Test viewing current boot logs with error priority: `journalctl -b -p err`."
        ]
    },
    "0700-story-section": {
        "slug": "story_section",
        "title": "Story Section: Disk Space Emergency & The WAR Meeting",
        "description": "Join Bob as a large file download fails with 'no space on device'. Discover why his 128GB SSD only displays 50GB in df, meet Mohan the resident Storage Admin, and discover the mysterious Project Sapphire WAR meeting.",
        "objectives": [
            "Understand real-world storage troubleshooting triggers ('no space on device' errors).",
            "Learn why df (disk free) reports mounted filesystem capacities rather than raw physical disk capacity.",
            "Understand the role of a Storage Administrator managing enterprise storage arrays, SAN, and NAS.",
            "Discover the meaning and function of an engineering WAR (Work at Risk) Room during project escalations.",
            "Prepare for mastering Linux storage architectures: Block devices, Partitioning, Filesystems, NAS, SAN, NFS, and LVM."
        ],
        "key_concepts": [
            {
                "term": "Filesystem Capacity vs. Physical Disk Capacity",
                "explanation": "The `df` command only reports mounted filesystems known to the kernel. If a 128GB physical disk only has a 50GB partition created and mounted, `df` will show 50GB in total. The remaining 78GB exists as raw unallocated space on the physical block device."
            },
            {
                "term": "The 'No Space on Device' Error",
                "explanation": "This critical kernel error occurs when an operation attempts to allocate blocks on a filesystem that has reached 100% capacity (or has exhausted its available inode pool). Immediate triage involves running `df -h` to find the saturated mount and `du -sh` to locate culprit files."
            },
            {
                "term": "The Enterprise Storage Administrator",
                "explanation": "In corporate infrastructure, Storage Admins oversee centralized high-availability appliances (SAN/NAS), allocate storage pools, provision LUNs to servers, manage disaster recovery replication, and prevent production out-of-space outages."
            },
            {
                "term": "The WAR (Work at Risk) Meeting",
                "explanation": "When mission-critical projects encounter severe risk, technical blockers, or imminent deadlines, teams convene in dedicated 'War Rooms' for full-day, cross-functional crisis management until critical risks are mitigated."
            }
        ],
        "commands": [
            {
                "cmd": "df -h",
                "desc": "Display mounted filesystem disk usage in human-readable units (GB, MB).",
                "example": "df -h",
                "options": "Shows Size, Used, Avail, Use%, and Mounted on"
            },
            {
                "cmd": "lsblk",
                "desc": "List all block devices, physical disks, and partitions to identify unallocated space.",
                "example": "lsblk",
                "options": "Shows device tree, disk size, and partition mount points"
            },
            {
                "cmd": "du -sh /home/*",
                "desc": "Calculate total disk space consumed by directories inside /home.",
                "example": "du -sh /home/*",
                "options": "`-s` summary, `-h` human-readable"
            }
        ],
        "exercises": [
            "Run `df -h` on your terminal to inspect all mounted filesystems and their utilization percentages.",
            "Compare `df -h` output with `lsblk` to verify whether all physical disk space is partitioned and mounted.",
            "Identify the top 5 largest directories in your home folder: `du -ah ~ 2>/dev/null | sort -rh | head -n 5`."
        ]
    },
    "0720-disk-partitions": {
        "slug": "disk_partitions",
        "title": "Disk Partitions, MBR vs GPT Schemes, and Partitioning with fdisk & gdisk",
        "description": "Master Linux block storage fundamentals: identify SCSI block devices (/dev/sd*), understand major and minor device numbers, contrast legacy MBR with modern GPT partition tables, and create GPT partitions using gdisk.",
        "objectives": [
            "Understand block devices in Linux (/dev/sd*, /dev/nvme*) and identify them in /dev/.",
            "Interpret block device major numbers (e.g., 8 for SCSI devices) and minor numbers (disk vs partition).",
            "Differentiate between the 3 partition types: Primary, Extended, and Logical partitions.",
            "Contrast Master Boot Record (MBR) limitations (4 primary partitions, 2TB limit) with GUID Partition Table (GPT) advantages (unlimited partitions, 2TB+ disks).",
            "Inspect partition tables using lsblk, fdisk -l, and gdisk -l.",
            "Interactively partition a disk using gdisk (new partition, Linux filesystem type 8300, write changes)."
        ],
        "key_concepts": [
            {
                "term": "Block Devices & /dev Special Files",
                "explanation": "Block devices transfer data in fixed chunks (blocks, typically 512 bytes or 4KB). In `ls -l /dev/`, they are identified by the leading `b`. Disks (`sda`, `sdb`) and partitions (`sda1`, `sdb1`) are block devices."
            },
            {
                "term": "Major and Minor Device Numbers",
                "explanation": "Every block device is identified by two numbers: `Major:Minor`.\n• **Major Number** (e.g. `8`): Identifies the device driver / subsystem (8 indicates SCSI/SATA disk driver, which assigns `/dev/sd*` names).\n• **Minor Number**: Distinguishes individual physical drives and their partitions (`sda` = 8:0, `sda1` = 8:1, `sdb` = 8:16)."
            },
            {
                "term": "Partition Types: Primary, Extended, Logical",
                "explanation": "• **Primary Partition**: Standalone bootable partition. MBR supports a maximum of 4 primary partitions.\n• **Extended Partition**: A special container partition created to bypass the 4-partition limit. It holds logical partitions.\n• **Logical Partitions**: Partitions created inside an extended partition."
            },
            {
                "term": "MBR vs GPT Partitioning Schemes",
                "explanation": "• **MBR (Master Boot Record)**: Legacy standard (>30 years old). Max 4 primary partitions, max 2TB disk size.\n• **GPT (GUID Partition Table)**: Modern UEFI standard. Supports disks larger than 2TB (up to zettabytes). Allows 128 partitions in Linux (theoretically unlimited). Always the recommended choice for modern systems."
            },
            {
                "term": "Partitioning Tools: fdisk vs gdisk",
                "explanation": "• `fdisk`: Traditional command-line utility for managing MBR partition tables.\n• `gdisk` (GPT fdisk): Dedicated menu-driven tool designed specifically for GUID Partition Tables (GPT)."
            }
        ],
        "commands": [
            {
                "cmd": "lsblk",
                "desc": "List block devices in a hierarchical tree showing sizes, types (disk/part), and mount points.",
                "example": "lsblk",
                "options": "Add `-m` for permissions or `-f` for filesystems"
            },
            {
                "cmd": "sudo fdisk -l",
                "desc": "Print detailed partition tables, sector sizes, and disk identifiers for all disks.",
                "example": "sudo fdisk -l",
                "options": "Can specify target disk: `sudo fdisk -l /dev/sda`"
            },
            {
                "cmd": "sudo gdisk /dev/<disk>",
                "desc": "Launch interactive GPT partition editor on target disk.",
                "example": "sudo gdisk /dev/sdb",
                "options": "`?` help, `p` print, `n` new partition, `w` write, `q` quit"
            },
            {
                "cmd": "sudo gdisk -l /dev/<disk>",
                "desc": "Display GPT partition table information non-interactively.",
                "example": "sudo gdisk -l /dev/sdb",
                "options": "`-l` list partition layout"
            }
        ],
        "exercises": [
            "Run `lsblk` and identify which block device represents your primary OS disk and how many partitions it contains.",
            "Inspect device numbers for your disks and partitions: `ls -l /dev/sd*` (or `/dev/nvme*`). Note the major and minor numbers.",
            "Run `sudo fdisk -l` and determine whether your partition table is `gpt` or `dos` (MBR).",
            "Simulate running `sudo gdisk /dev/sdb` (on a test/spare disk or loop device): press `p` to view, `n` to create a partition with type `8300`, and `q` to quit without saving."
        ]
    },
    "0740-file-systems-in-linux": {
        "slug": "file_systems_in_linux",
        "title": "Linux File Systems: EXT2, EXT3, EXT4, mkfs, Mounting, and /etc/fstab",
        "description": "Understand why raw partitions need filesystems before storing data. Compare the EXT family (EXT2, EXT3, EXT4), format partitions with mkfs.ext4, mount filesystems, and configure persistent boot mounts in /etc/fstab.",
        "objectives": [
            "Understand why raw partitions require a filesystem to organize and store files.",
            "Compare EXT2 (non-journaled), EXT3 (journaled), and EXT4 (extents, 16TB file / 1EB volume limits, backward compatibility).",
            "Format a partition with an EXT4 filesystem using mkfs.ext4.",
            "Mount filesystems to directory mount points with mount and unmount with umount.",
            "Verify active mounts using df -hT and mount.",
            "Configure permanent boot mounts in /etc/fstab and understand all 6 fields (device, mount point, type, options, dump, pass)."
        ],
        "key_concepts": [
            {
                "term": "Raw Partitions vs. Filesystems",
                "explanation": "A partition without a filesystem is just raw, unformatted blocks of storage. A filesystem creates internal data structures (inodes, superblocks, allocation bitmaps, directory trees) that allow the operating system to create, find, read, and write files."
            },
            {
                "term": "EXT Series Comparison: EXT2 vs EXT3 vs EXT4",
                "explanation": "• **EXT2**: Fast, but non-journaled. After a crash or power cut, system boot is delayed by lengthy `fsck` consistency checks. Max 2TB file, 4TB volume.\n• **EXT3**: Added journaling (recording metadata transactions before writing to disk). Enables rapid crash recovery. Backward compatible with EXT2.\n• **EXT4**: Modern standard. Supports 16TB files and 1 Exabyte volumes. Uses extents (contiguous block allocations) to reduce fragmentation and improve performance. Backward compatible with EXT2 and EXT3."
            },
            {
                "term": "Mounting and Unmounting",
                "explanation": "In Linux, storage devices are not assigned drive letters (like C: or D:). Instead, a formatted filesystem is attached to an existing empty directory in the single root (`/`) hierarchy using the `mount` command. Detaching is done via `umount`."
            },
            {
                "term": "The 6 Fields of /etc/fstab",
                "explanation": "Each line in `/etc/fstab` defines a persistent mount with 6 space-separated fields:\n1. **Filesystem**: Device path (`/dev/sdb1`) or UUID (`UUID=...`).\n2. **Mount Point**: Target directory (e.g. `/media/data`).\n3. **Type**: Filesystem type (`ext4`, `xfs`, `nfs`).\n4. **Options**: Mount settings (`defaults`, `rw`, `ro`, `noexec`).\n5. **Dump**: Backup utility flag (`0` = disable backup, `1` = enable).\n6. **Pass**: `fsck` boot check order (`0` = ignore, `1` = root filesystem check first, `2` = other local filesystems)."
            }
        ],
        "commands": [
            {
                "cmd": "sudo mkfs.ext4 /dev/<partition>",
                "desc": "Format a partition with an EXT4 filesystem.",
                "example": "sudo mkfs.ext4 /dev/sdb1",
                "options": "Creates inodes, journal, and superblock"
            },
            {
                "cmd": "sudo mount /dev/<partition> <mount_dir>",
                "desc": "Mount formatted filesystem to a directory mount point.",
                "example": "sudo mount /dev/sdb1 /mnt/data",
                "options": "Attach filesystem to directory tree"
            },
            {
                "cmd": "sudo umount <mount_dir>",
                "desc": "Unmount filesystem from directory mount point.",
                "example": "sudo umount /mnt/data",
                "options": "Safely flushes cached writes and detaches"
            },
            {
                "cmd": "df -hT",
                "desc": "Display mounted filesystems with usage percentages and filesystem types.",
                "example": "df -hT",
                "options": "`-h` human-readable, `-T` show filesystem type"
            },
            {
                "cmd": "sudo mount -a",
                "desc": "Mount all filesystems defined in /etc/fstab (vital test to catch syntax errors).",
                "example": "sudo mount -a",
                "options": "Reads `/etc/fstab` entries"
            },
            {
                "cmd": "blkid",
                "desc": "Locate block device UUIDs and filesystem type signatures.",
                "example": "sudo blkid /dev/sdb1",
                "options": "Prints UUID, TYPE, and PARTUUID"
            }
        ],
        "exercises": [
            "Check all mounted filesystems and their types on your system: `df -hT`.",
            "Inspect your system's `/etc/fstab` file: `cat /etc/fstab` and identify the 6 fields on each line.",
            "Display the UUID of all available block devices: `sudo blkid`.",
            "Create a temporary mount directory: `sudo mkdir -p /mnt/testdata` and practice verifying `/etc/fstab` syntax with `sudo mount -a`."
        ]
    },
    "0760-das-nas-and-san": {
        "slug": "das_nas_and_san",
        "title": "Enterprise External Storage: DAS vs NAS vs SAN, LUNs, and Fibre Channel",
        "description": "Compare enterprise storage architectures: Direct Attached Storage (DAS), Network Attached Storage (NAS), and Storage Area Networks (SAN). Understand block vs file storage, LUN provisioning, Host Bus Adapters (HBA), and Fibre Channel switches.",
        "objectives": [
            "Understand why enterprise environments require dedicated external, high-availability storage.",
            "Compare the 3 major storage architectures: Direct Attached Storage (DAS), Network Attached Storage (NAS), and Storage Area Network (SAN).",
            "Differentiate between Block Storage (DAS, SAN) and File Storage (NAS/NFS).",
            "Understand SAN components: LUNs (Logical Unit Numbers), Fibre Channel Protocol (FCP), FC Switches, and Host Bus Adapters (HBA).",
            "Identify appropriate use cases for NAS (shared web files) vs SAN (Oracle, PostgreSQL, VMware, Hyper-V)."
        ],
        "key_concepts": [
            {
                "term": "Direct Attached Storage (DAS)",
                "explanation": "Storage attached directly to a single host computer via SATA, SAS, or SCSI cables with no network or firewall in between. Provides outstanding speed and lowest cost, but cannot be shared between multiple servers, making it unsuitable for large multi-server clusters."
            },
            {
                "term": "Network Attached Storage (NAS)",
                "explanation": "File-level storage connected across standard IP Ethernet networks (typically using NFS or SMB). Storage is presented to client hosts as a shared directory/folder. Multiple servers can read and write simultaneously. Ideal for central file shares and web application backends, but higher latency makes it non-ideal for heavy production database transaction logs."
            },
            {
                "term": "Storage Area Network (SAN)",
                "explanation": "A specialized, high-speed, dedicated network (using Fibre Channel Protocol or iSCSI) connecting servers to centralized enterprise storage arrays. SAN delivers raw block storage with ultra-high throughput and microsecond latency, making it the industry standard for production databases (Oracle, PostgreSQL, MS SQL) and hypervisors (VMware, KVM)."
            },
            {
                "term": "LUN (Logical Unit Number)",
                "explanation": "A unique identifier assigned to a carved slice of block storage from a SAN storage pool. When provisioned, the host operating system sees the LUN as a physical raw hard disk (`/dev/sd*`) that can be partitioned and formatted."
            },
            {
                "term": "Fibre Channel (FC) & Host Bus Adapter (HBA)",
                "explanation": "SANs typically use Fibre Channel switches and optical fiber cables. Servers connect to the SAN switch using a specialized PCIe card called a Host Bus Adapter (HBA), offloading storage protocol processing from the server CPU."
            }
        ],
        "commands": [
            {
                "cmd": "lsscsi",
                "desc": "List SCSI, SATA, and SAN storage devices along with their assigned LUN numbers.",
                "example": "lsscsi",
                "options": "Shows transport address, device name, and LUN ID"
            },
            {
                "cmd": "systool -c fc_host -v",
                "desc": "Inspect Fibre Channel Host Bus Adapter (HBA) port speeds, status, and World Wide Names (WWN).",
                "example": "systool -c fc_host -v",
                "options": "Displays HBA hardware details"
            },
            {
                "cmd": "multipath -ll",
                "desc": "Display redundant multipath SAN storage links to prevent single-cable failovers.",
                "example": "sudo multipath -ll",
                "options": "Shows active and standby storage paths"
            }
        ],
        "exercises": [
            "Check for installed SCSI and disk controller hardware on your system: `lspci | grep -i -E 'scsi|sata|nvme|storage'`.",
            "Inspect disk identifiers under `/dev/disk/by-id/`: `ls -l /dev/disk/by-id/` to see how hardware serials map to `/dev/sd*`.",
            "Compare the characteristics of DAS, NAS, and SAN: write a comparison table showing Architecture, Protocol, Storage Type (Block vs File), and Primary Use Case."
        ]
    },
    "0765-nfs-filesystem": {
        "slug": "nfs_filesystem",
        "title": "Network File System (NFS): Server Exports, Client Mounting, and /etc/exports",
        "description": "Implement file-level network sharing with NFS. Configure /etc/exports on the NFS server, export shares with exportfs, open firewall ports, and mount remote network directories onto Linux clients.",
        "objectives": [
            "Understand the NFS client-server model and file-level network storage sharing.",
            "Configure shared directories in /etc/exports on the NFS server.",
            "Understand export options: rw, ro, sync, no_subtree_check, and root_squash.",
            "Export directories dynamically using exportfs -a and inspect with exportfs -v.",
            "Mount remote NFS shares on client systems using mount -t nfs <server_ip>:<path> <mount_dir>.",
            "Understand firewall and networking requirements (RPC port 111, NFS port 2049).",
            "Configure persistent NFS mounting in /etc/fstab using the _netdev mount option."
        ],
        "key_concepts": [
            {
                "term": "NFS Architecture & File-Level Sharing",
                "explanation": "Unlike block storage where raw disk blocks are transmitted, NFS transmits filesystem operations over the network (RPC). The client does not format the drive; it mounts a directory tree that is physically managed by the remote NFS server."
            },
            {
                "term": "The /etc/exports Configuration File",
                "explanation": "The central file on the NFS server defining which directories are shared and which clients can access them:\n`/software/repos 10.61.35.0/24(rw,sync,no_subtree_check)`\nClients can be specified by single IP (`10.61.35.201`), IP subnet CIDR (`10.61.35.0/24`), hostname (`node01.lan`), or wildcard (`*`)."
            },
            {
                "term": "The exportfs Command",
                "explanation": "• `sudo exportfs -a`: Exports all directories listed in `/etc/exports`.\n• `sudo exportfs -r`: Re-exports shares after modifying `/etc/exports` without restarting the NFS service.\n• `sudo exportfs -v`: Verbose listing showing active export paths and applied permissions.\n• `sudo exportfs -u <client>:<dir>`: Un-exports a specific share."
            },
            {
                "term": "Client Mounting Syntax & _netdev",
                "explanation": "Clients mount NFS shares using:\n`sudo mount -t nfs <nfs_server_ip>:/remote/path /local/mount/point`\nWhen adding an NFS mount to `/etc/fstab`, always include the `_netdev` option: it instructs the systemd boot process to delay mounting until network connectivity is fully established."
            }
        ],
        "commands": [
            {
                "cmd": "sudo exportfs -a",
                "desc": "Export all directories defined in /etc/exports on the NFS server.",
                "example": "sudo exportfs -a",
                "options": "Updates kernel NFS export table"
            },
            {
                "cmd": "sudo exportfs -v",
                "desc": "Display verbose list of all actively exported shares and active permissions.",
                "example": "sudo exportfs -v",
                "options": "Shows applied options like rw, sync, etc."
            },
            {
                "cmd": "sudo exportfs -r",
                "desc": "Re-export all shares, refreshing changes made to /etc/exports without restarting service.",
                "example": "sudo exportfs -r",
                "options": "Re-synchronizes export list"
            },
            {
                "cmd": "showmount -e <nfs_server>",
                "desc": "Query an NFS server from a client to list all exported shares available for mounting.",
                "example": "showmount -e 10.61.112.101",
                "options": "`-e` show export list"
            },
            {
                "cmd": "sudo mount -t nfs <server>:<remote_path> <local_mount>",
                "desc": "Mount remote NFS export onto client local directory.",
                "example": "sudo mount -t nfs 10.61.112.101:/software/repos /mnt/software/repos",
                "options": "`-t nfs` specifies NFS filesystem type"
            }
        ],
        "exercises": [
            "Check if NFS client tools are installed on your machine: `which showmount` or `which mount.nfs`.",
            "Inspect the contents of `/etc/exports` (if installed) or review its manual: `man 5 exports`.",
            "Simulate adding an NFS mount to `/etc/fstab`: `10.61.112.101:/software/repos /mnt/software/repos nfs defaults,_netdev 0 0`.",
            "Understand why `_netdev` is required in `/etc/fstab` for network mounts during system boot."
        ]
    },
    "0770-lvm": {
        "slug": "logical_volume_manager_lvm",
        "title": "Logical Volume Management (LVM): Physical Volumes, Volume Groups, and Resizing",
        "description": "Master dynamic storage pooling with LVM. Construct Physical Volumes (pvcreate), aggregate disks into Volume Groups (vgcreate), carve out Logical Volumes (lvcreate), and expand filesystems live with lvextend and resize2fs without downtime.",
        "objectives": [
            "Understand the 3-tier LVM architecture: Physical Volumes (PV) → Volume Groups (VG) → Logical Volumes (LV).",
            "Install and verify the lvm2 storage management package.",
            "Initialize raw disks or partitions into Physical Volumes using pvcreate and inspect with pvs and pvdisplay.",
            "Combine multiple physical volumes into a Volume Group pool using vgcreate and inspect with vgs and vgdisplay.",
            "Carve out Logical Volumes from volume groups using lvcreate and inspect with lvs and lvdisplay.",
            "Format logical volumes with mkfs.ext4 and mount them at a directory mount point.",
            "Understand dual device paths: /dev/<vg_name>/<lv_name> and /dev/mapper/<vg_name>-<lv_name>.",
            "Dynamically increase a logical volume with lvextend and expand the underlying filesystem live using resize2fs without unmounting or downtime."
        ],
        "key_concepts": [
            {
                "term": "The 3 Layers of LVM Architecture",
                "explanation": "• **Physical Volume (PV)**: An underlying block device (disk or partition, e.g. `/dev/sdb`) initialized with LVM metadata.\n• **Volume Group (VG)**: A unified storage pool created by combining one or more PVs. Acts as a virtual disk pool.\n• **Logical Volume (LV)**: A slice of storage carved out from a VG. Functions just like a traditional partition, but can span multiple physical disks and be resized on the fly."
            },
            {
                "term": "Live Resizing Without Downtime",
                "explanation": "Traditional partitions have static boundaries: extending them requires stopping services, taking filesystems offline, and risking data loss. LVM logical volumes can be expanded dynamically while the filesystem is mounted and actively servicing read/write traffic!"
            },
            {
                "term": "The 2-Step Storage Expansion Workflow",
                "explanation": "Expanding storage requires two distinct actions:\n1. **Expand the Block Container (LV)**: `lvextend -L +1G /dev/Kelston_VG/vol1` (allocates additional extents from the VG).\n2. **Expand the Filesystem**: `resize2fs /dev/Kelston_VG/vol1` (tells the EXT4 filesystem to recognize and utilize the newly allocated space)."
            },
            {
                "term": "/dev/mapper vs /dev/<VG>/<LV>",
                "explanation": "Linux Device Mapper creates the actual device node under `/dev/mapper/<VG>-<LV>`. LVM simultaneously creates a friendly symbolic link under `/dev/<VG>/<LV>`. Both point to the exact same block storage device."
            }
        ],
        "commands": [
            {
                "cmd": "sudo pvcreate /dev/<device>",
                "desc": "Initialize a raw disk or partition as an LVM Physical Volume.",
                "example": "sudo pvcreate /dev/sdb",
                "options": "Writes LVM label and metadata"
            },
            {
                "cmd": "sudo pvs / sudo pvdisplay",
                "desc": "List summary or detailed attributes of all Physical Volumes.",
                "example": "sudo pvs",
                "options": "Shows PV name, VG membership, and size"
            },
            {
                "cmd": "sudo vgcreate <vg_name> /dev/<device>",
                "desc": "Create a Volume Group pool from one or more Physical Volumes.",
                "example": "sudo vgcreate Kelston_VG /dev/sdb",
                "options": "Can combine multiple PVs: `vgcreate my_vg /dev/sdb /dev/sdc`"
            },
            {
                "cmd": "sudo vgs / sudo vgdisplay",
                "desc": "List summary or detailed attributes of Volume Groups.",
                "example": "sudo vgs",
                "options": "Shows total size and free unallocated pool space"
            },
            {
                "cmd": "sudo lvcreate -L <size> -n <lv_name> <vg_name>",
                "desc": "Create a new Logical Volume from a Volume Group.",
                "example": "sudo lvcreate -L 1G -n vol1 Kelston_VG",
                "options": "`-L` size (e.g. 1G, 500M), `-n` volume name"
            },
            {
                "cmd": "sudo lvs / sudo lvdisplay",
                "desc": "List summary or detailed attributes of Logical Volumes.",
                "example": "sudo lvs",
                "options": "Shows LV name, VG name, and logical size"
            },
            {
                "cmd": "sudo lvextend -L +<size> /dev/<vg>/<lv>",
                "desc": "Increase Logical Volume capacity by adding space from the Volume Group.",
                "example": "sudo lvextend -L +1G /dev/Kelston_VG/vol1",
                "options": "`+1G` increases by 1GB; can use `-r` to auto-resize filesystem"
            },
            {
                "cmd": "sudo resize2fs /dev/<vg>/<lv>",
                "desc": "Expand EXT2/EXT3/EXT4 filesystem on the fly to fill the resized logical volume.",
                "example": "sudo resize2fs /dev/Kelston_VG/vol1",
                "options": "Performs live on-line resize without unmounting"
            }
        ],
        "exercises": [
            "Check if your current Linux installation uses LVM: run `sudo pvs`, `sudo vgs`, and `sudo lvs`.",
            "Inspect `lsblk` and identify any devices with type `lvm`.",
            "Write down the step-by-step commands to create a 2GB LV named `weblv` in a VG named `appvg` from disk `/dev/sdb`.",
            "Explain the difference between `lvextend` and `resize2fs`, and why both steps are required when growing an LVM volume."
        ]
    },
    "0800-story-section": {
        "slug": "story_section",
        "title": "Story Section: Project Mercury Demo & The Status Meeting Pressure",
        "description": "Four days before the client demonstration, Bob showcases the working Django web application on his laptop. While Andrew praises the progress, Donald pushes back with last-minute client feature requests.",
        "objectives": [
            "Review Bob's progress: migrating and stabilizing the Django web application on Linux after mastering services, networking, and storage.",
            "Understand team dynamics in engineering projects: handling stakeholder praise, peer feedback, and scope creep.",
            "Learn strategies for handling last-minute feature additions under tight deadlines.",
            "Connect Linux system administration skills (services, storage, networking) directly to software engineering project success."
        ],
        "key_concepts": [
            {
                "term": "Milestone Deliverables & Live Demos",
                "explanation": "Successfully demonstrating a working application in local and staging environments requires rock-solid Linux infrastructure health: adequate disk space, stable systemd background services, and correct network socket bindings."
            },
            {
                "term": "Scope Creep & Late Feature Requests",
                "explanation": "When new client requests arrive days before a demo, team leads (Andrew) and project managers (Amira) must track and prioritize tasks to prevent deployment instability while keeping clients satisfied."
            },
            {
                "term": "Working Under Pressure in Engineering Teams",
                "explanation": "Engineering teams often face demanding colleagues (Donald) and tight turnarounds. Deep proficiency in Linux troubleshooting empowers engineers to rapidly distinguish infrastructure bottlenecks from application code bugs."
            }
        ],
        "commands": [
            {
                "cmd": "git status",
                "desc": "Check local source code repository status, staged files, and branch health.",
                "example": "git status",
                "options": "Shows modified, staged, and untracked files"
            },
            {
                "cmd": "systemctl status project-mercury",
                "desc": "Verify that the background web application service is active and running cleanly.",
                "example": "systemctl status project-mercury",
                "options": "Displays service uptime, PID, and recent logs"
            },
            {
                "cmd": "df -h",
                "desc": "Ensure sufficient filesystem capacity exists for application logs and database transactions.",
                "example": "df -h",
                "options": "Verifies available disk space"
            }
        ],
        "exercises": [
            "Run `git status` on your project to review clean working tree states before milestone deliveries.",
            "Check system uptime and memory utilization: `uptime` and `free -h`.",
            "Summarize the complete Linux storage path: Raw Disks (`lsblk`) → Partitions (`gdisk`) → Filesystems (`mkfs.ext4`) → Mounts (`mount`, `/etc/fstab`) → LVM (`pvcreate`, `vgcreate`, `lvcreate`, `resize2fs`)."
        ]
    }
}


def clean_vtt_to_text(vtt_file_path: Path) -> Tuple[str, List[str]]:
    """
    Parses a WebVTT file and extracts a clean, readable transcript.
    Returns:
        (full_paragraph_text, list_of_raw_sentences)
    """
    lines = vtt_file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    
    cleaned_cues = []
    i = 0
    in_header = True
    
    # Regex patterns
    timestamp_re = re.compile(r'^\d{2}:(?:[0-5]\d):[0-5]\d(?:\.\d+)?\s*-->\s*\d{2}:(?:[0-5]\d):[0-5]\d(?:\.\d+)?|^\d{2}:[0-5]\d(?:\.\d+)?\s*-->\s*\d{2}:[0-5]\d(?:\.\d+)?')
    tag_re = re.compile(r'<[^>]+>')
    
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line:
            continue
            
        if in_header:
            if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            # If timestamp reached, header is done
            if timestamp_re.search(line):
                in_header = False
                continue
            # If line is numeric cue ID right before timestamp
            if line.isdigit() and i < len(lines) and timestamp_re.search(lines[i].strip()):
                in_header = False
                continue
            continue
            
        # Ignore cue index numbers
        if line.isdigit() and i < len(lines) and timestamp_re.search(lines[i].strip()):
            continue
            
        # Ignore timestamp lines
        if timestamp_re.search(line):
            continue
            
        # Strip HTML/VTT tags like <c.yellow> or <b>
        clean_line = tag_re.sub('', line).strip()
        
        # Strip leading bullet/hyphen from speaker change
        if clean_line.startswith('-'):
            clean_line = clean_line.lstrip('-').strip()
            
        if not clean_line:
            continue
            
        # Avoid immediate duplicate lines (common in rolling WebVTT subtitles)
        if cleaned_cues and cleaned_cues[-1] == clean_line:
            continue
            
        cleaned_cues.append(clean_line)
        
    # Join into coherent sentences and paragraphs
    raw_sentences = []
    current_sentence = []
    
    for cue in cleaned_cues:
        current_sentence.append(cue)
        # Check if cue ends with sentence-terminating punctuation
        if re.search(r'[.!?]["\']?$', cue):
            raw_sentences.append(" ".join(current_sentence))
            current_sentence = []
            
    if current_sentence:
        raw_sentences.append(" ".join(current_sentence))
        
    # Group sentences into well-paced paragraphs (3-5 sentences or on natural topic shifts)
    paragraphs = []
    cur_p = []
    
    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue
        cur_p.append(sent)
        # Break paragraph on dialogue shift or ~3-4 sentences
        if len(cur_p) >= 4 or (len(cur_p) >= 2 and ("Bob " in sent or "Now, " in sent or "Let's " in sent or "Finally," in sent)):
            paragraphs.append(" ".join(cur_p))
            cur_p = []
            
    if cur_p:
        paragraphs.append(" ".join(cur_p))
        
    full_text = "\n\n".join(paragraphs)
    return full_text, raw_sentences


def extract_key_terms_from_text(text: str) -> List[Dict[str, str]]:
    """
    Fallback extractor for unknown future VTT files:
    Finds common Linux commands and keywords mentioned in the text.
    """
    common_linux_tools = [
        "ls", "cd", "pwd", "mkdir", "rmdir", "cp", "mv", "rm", "touch", "cat",
        "more", "less", "head", "tail", "grep", "find", "chmod", "chown",
        "chgrp", "ps", "top", "kill", "systemctl", "journalctl", "tar", "gzip",
        "zip", "unzip", "ssh", "scp", "rsync", "curl", "wget", "ping", "netstat",
        "ip", "ifconfig", "df", "du", "free", "uname", "whoami", "sudo", "su",
        "useradd", "usermod", "groupadd", "echo", "export", "alias", "history",
        "type", "which", "whereis", "whatis", "man", "apropos"
    ]
    
    found_cmds = []
    lower_text = text.lower()
    
    for cmd in common_linux_tools:
        pattern = rf'\b{re.escape(cmd)}\b'
        if re.search(pattern, lower_text):
            found_cmds.append({
                "cmd": cmd,
                "desc": f"Linux command `{cmd}` referenced in this lecture.",
                "example": f"{cmd} --help",
                "options": "Refer to `man " + cmd + "` for options."
            })
            
    return found_cmds[:8]  # top 8


def normalize_title(filename: str) -> Tuple[str, str, str]:
    """
    Derives clean title, normalized key, and step folder name.
    Example input: '0125-introduction-to-linux-shell [461061073].en.vtt'
    Returns:
        (folder_slug_base, clean_title, lookup_key)
    """
    # Remove extension
    name = filename
    name = re.sub(r'\.en\.vtt$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\.vtt$', '', name, flags=re.IGNORECASE)
    # Remove bracketed IDs like [461061073]
    name = re.sub(r'\[.*?\]', '', name).strip()
    # Remove parenthesized phrases like (First Team meeting...)
    name = re.sub(r'\(.*?\)', '', name).strip()
    # Remove .mp4 if embedded in video filenames
    name = re.sub(r'\.mp4\b', '', name, flags=re.IGNORECASE).strip()
    
    # Match leading numbers like 0125 or 0150
    m = re.match(r'^(\d+)[-_ ]*(.*)$', name)
    if m:
        num_prefix = m.group(1)
        rest = m.group(2).strip()
    else:
        num_prefix = ""
        rest = name.strip()
        
    # Clean up words
    words = re.split(r'[-_ ]+', rest)
    clean_title = " ".join([w.capitalize() for w in words if w])
    slug = "_".join([w.lower() for w in words if w])
    
    lookup_key = f"{num_prefix}-{slug}".replace("_", "-") if num_prefix else slug.replace("_", "-")
    
    return slug, clean_title, lookup_key


def generate_markdown_guide(
    step_num: int,
    module_name: str,
    vtt_filename: str,
    clean_transcript: str,
    metadata: Optional[Dict] = None
) -> str:
    """
    Generates a rich, structured Markdown study guide for the step.
    """
    slug, auto_title, lookup_key = normalize_title(vtt_filename)
    
    # Check known metadata
    matched_meta = None
    if metadata:
        matched_meta = metadata
    else:
        # Check by lookup key, slug, or numeric prefix
        for k, v in KNOWN_LESSONS_METADATA.items():
            if k in lookup_key or lookup_key in k or slug in k or (len(lookup_key) >= 4 and k.startswith(lookup_key[:4])):
                matched_meta = v
                break
                
    title = matched_meta["title"] if matched_meta else auto_title
    description = matched_meta["description"] if matched_meta else f"Study guide and reference notes for {title}."
    
    md_lines = []
    
    # Header
    md_lines.append(f"# Step {step_num:02d}: {title}")
    md_lines.append("")
    md_lines.append(f"> **Module:** {module_name.replace('_', ' ').title()}  ")
    md_lines.append(f"> **Source Lecture:** `{vtt_filename}`  ")
    md_lines.append(f"> **Target Audience:** Linux Beginners & System Administrators")
    md_lines.append("")
    md_lines.append(f"_{description}_")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    
    # 1. Objectives
    md_lines.append("## 🎯 Learning Objectives")
    md_lines.append("")
    if matched_meta and "objectives" in matched_meta:
        for obj in matched_meta["objectives"]:
            md_lines.append(f"- [ ] {obj}")
    else:
        md_lines.append(f"- [ ] Understand the core concepts introduced in **{title}**.")
        md_lines.append("- [ ] Run and practice the commands demonstrated in the lecture.")
        md_lines.append("- [ ] Review key syntax, flags, and common real-world use cases.")
    md_lines.append("")
    
    # 2. Key Concepts
    md_lines.append("## 💡 Key Concepts & Explanations")
    md_lines.append("")
    if matched_meta and "key_concepts" in matched_meta:
        for item in matched_meta["key_concepts"]:
            md_lines.append(f"### {item['term']}")
            md_lines.append(f"{item['explanation']}")
            md_lines.append("")
    else:
        md_lines.append("### Core Lecture Principles")
        # Extract first paragraph as conceptual foundation
        paras = clean_transcript.split("\n\n")
        intro_para = paras[0] if paras else "In this lesson, we explore foundational Linux terminal operations."
        md_lines.append(intro_para)
        md_lines.append("")
        
    # 3. Command Reference & Syntax
    md_lines.append("## 💻 Command Reference & Syntax")
    md_lines.append("")
    
    commands_to_show = []
    if matched_meta and "commands" in matched_meta:
        commands_to_show = matched_meta["commands"]
    else:
        commands_to_show = extract_key_terms_from_text(clean_transcript)
        
    if commands_to_show:
        md_lines.append("| Command / Syntax | Purpose | Key Options / Flags |")
        md_lines.append("| :--- | :--- | :--- |")
        for cmd in commands_to_show:
            c_syntax = cmd['cmd'].replace('|', '\\|')
            c_desc = cmd['desc'].replace('|', '\\|')
            c_opt = cmd.get('options', '-').replace('|', '\\|')
            md_lines.append(f"| `{c_syntax}` | {c_desc} | {c_opt} |")
        md_lines.append("")
        
        md_lines.append("### Command Usage Examples")
        md_lines.append("```bash")
        for cmd in commands_to_show:
            md_lines.append(f"# {cmd['desc']}")
            md_lines.append(cmd['example'])
            md_lines.append("")
        md_lines.append("```")
        md_lines.append("")
    else:
        md_lines.append("_No specific standalone CLI commands were detected in this overview video._")
        md_lines.append("")
        
    # 4. Hands-on Practice
    md_lines.append("## 🛠️ Hands-on Practice Exercises")
    md_lines.append("")
    md_lines.append("Practice these commands directly in your terminal to build muscle memory:")
    md_lines.append("")
    if matched_meta and "exercises" in matched_meta:
        for idx, ex in enumerate(matched_meta["exercises"], 1):
            md_lines.append(f"{idx}. {ex}")
    else:
        md_lines.append("1. Open your Linux terminal session.")
        md_lines.append("2. Execute each command mentioned in the syntax table above.")
        md_lines.append("3. Use the `--help` flag with each command to view its official syntax manual.")
    md_lines.append("")
    
    # 5. Full Clean Transcript
    md_lines.append("## 📖 Full Lecture Transcript (Cleaned & Formatted)")
    md_lines.append("")
    md_lines.append("<details>")
    md_lines.append("<summary><b>Click to expand the complete word-for-word lecture text</b></summary>")
    md_lines.append("")
    md_lines.append(clean_transcript)
    md_lines.append("")
    md_lines.append("</details>")
    md_lines.append("")
    
    # 6. Summary Notes
    md_lines.append("## 📝 Summary & Key Takeaways")
    md_lines.append("")
    if matched_meta and "objectives" in matched_meta:
        for obj in matched_meta["objectives"]:
            # Convert objective to learned assertion
            learned = obj.replace("Understand", "Understood").replace("Learn", "Learned").replace("Compare", "Compared")
            md_lines.append(f"- ✅ **{learned}**")
    else:
        md_lines.append(f"- ✅ Completed the **{title}** lesson.")
        md_lines.append("- ✅ Reviewed all lecture explanations and terminal examples.")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append(f"[← Back to Linux Basics Curriculum](../README.md)")
    md_lines.append("")
    
    return "\n".join(md_lines)


def generate_master_readme(output_dir: Path, steps_catalog: List[Dict]) -> str:
    """
    Generates the master index README.md for the linux_basics folder.
    """
    lines = []
    lines.append("# 🐧 Linux Basics: Complete Beginner-to-Pro Study Guide")
    lines.append("")
    lines.append("Welcome to the **Linux Basics** curriculum! This repository contains structured study guides, command cheat sheets, concept breakdowns, and practice exercises extracted directly from the video course lectures.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📚 Course Curriculum & Step-by-Step Index")
    lines.append("")
    lines.append("| Step | Topic / Lesson | Module | Study Guide Link |")
    lines.append("| :--- | :--- | :--- | :--- |")
    
    for item in steps_catalog:
        step_num = item["step_num"]
        title = item["title"]
        module = item["module"].replace('_', ' ').title()
        folder_name = item["folder_name"]
        lines.append(f"| `Step {step_num:02d}` | **{title}** | {module} | [📖 Open Study Guide](./{folder_name}/README.md) |")
        
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🚀 How to Use This Guide")
    lines.append("")
    lines.append("1. **Follow the Steps in Order:** Start with `step01` and progress sequentially.")
    lines.append("2. **Type Out Every Command:** Do not simply copy-paste. Typing commands into your terminal builds muscle memory.")
    lines.append("3. **Complete the Practice Exercises:** Every lesson includes hands-on tasks to test your understanding.")
    lines.append("4. **Consult the Full Transcripts:** If any concept is unclear, expand the full transcript section inside each study guide to read the instructor's detailed explanation.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🔄 Updating / Regenerating the Guides")
    lines.append("")
    lines.append("This entire directory is generated by `extract_linux_guides.py`.")
    lines.append("Whenever new subtitles (`.vtt` files) or modules are added under `linux subtitles/`, simply run:")
    lines.append("```bash")
    lines.append("python extract_linux_guides.py")
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)


ACTIVE_MODULES = [
    "working_with_shell",
    "linux_core_concepts",
    "package_management",
    "working_with_shell_2",
    "security_and_file_permission",
    "networking",
    "service_management_with_systemD",
    "storage_in_linux",
]


def process_subtitles(
    subtitles_root: Path,
    output_root: Path,
    target_module: Optional[str] = None
) -> List[Dict]:
    """
    Scans subtitles_root, iterates over module subdirectories and VTT files,
    cleans transcripts, and writes step folders into output_root.
    """
    if not subtitles_root.exists():
        raise FileNotFoundError(f"Subtitles directory not found at: {subtitles_root}")
        
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Discover module directories and sort by chronological lecture order
    def get_module_sort_key(d: Path) -> int:
        vtt_files = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() == '.vtt']
        min_num = 999999
        for f in vtt_files:
            m = re.match(r'^(\d+)', f.name)
            if m:
                min_num = min(min_num, int(m.group(1)))
        return min_num

    module_dirs = [d for d in subtitles_root.iterdir() if d.is_dir()]
    if target_module:
        module_dirs = [d for d in module_dirs if d.name == target_module]
        if not module_dirs:
            raise ValueError(f"Target module '{target_module}' not found in {subtitles_root}")
    elif ACTIVE_MODULES:
        module_dirs = [d for d in module_dirs if d.name in ACTIVE_MODULES]
        
    module_dirs.sort(key=get_module_sort_key)
            
    print(f"[*] Found {len(module_dirs)} module directory(ies) in '{subtitles_root.name}':")
    for d in module_dirs:
        print(f"    - {d.name}")
        
    global_step = 1
    catalog = []
    
    for mod_dir in module_dirs:
        print(f"\n[+] Processing module: '{mod_dir.name}'...")
        vtt_files = [f for f in mod_dir.iterdir() if f.is_file() and f.suffix.lower() == '.vtt']
        # Sort naturally by filename
        vtt_files.sort(key=lambda f: f.name)
        
        if not vtt_files:
            print(f"    [!] No .vtt files found in {mod_dir.name}, skipping.")
            continue
            
        for vtt_file in vtt_files:
            slug, title, lookup_key = normalize_title(vtt_file.name)
            
            # Find metadata if available
            meta = None
            for k, v in KNOWN_LESSONS_METADATA.items():
                if k in lookup_key or lookup_key in k or slug in k or (len(lookup_key) >= 4 and k.startswith(lookup_key[:4])):
                    meta = v
                    title = v["title"]
                    break
                    
            if meta and "slug" in meta:
                slug = meta["slug"]
                
            folder_name = f"step{global_step:02d}_{slug}"
            step_dir = output_root / folder_name
            step_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"    -> Step {global_step:02d}: {title} ({vtt_file.name})")
            
            # Clean VTT
            clean_text, _ = clean_vtt_to_text(vtt_file)
            
            # Generate Study Guide Markdown
            guide_md = generate_markdown_guide(
                step_num=global_step,
                module_name=mod_dir.name,
                vtt_filename=vtt_file.name,
                clean_transcript=clean_text,
                metadata=meta
            )
            
            readme_path = step_dir / "README.md"
            readme_path.write_text(guide_md, encoding="utf-8")
            
            catalog.append({
                "step_num": global_step,
                "title": title,
                "module": mod_dir.name,
                "folder_name": folder_name,
                "vtt_file": vtt_file.name
            })
            
            global_step += 1
            
    # Clean up obsolete step directories not in current catalog
    active_folders = {item["folder_name"] for item in catalog}
    for item in output_root.iterdir():
        if item.is_dir() and item.name.startswith("step") and item.name not in active_folders:
            import shutil
            shutil.rmtree(item)

    # Generate Master README
    master_readme_content = generate_master_readme(output_root, catalog)
    master_readme_path = output_root / "README.md"
    master_readme_path.write_text(master_readme_content, encoding="utf-8")
    print(f"\n[OK] Generated Master Curriculum Index: {master_readme_path}")
    print(f"[OK] Successfully generated {len(catalog)} step-by-step Linux study guide(s) inside '{output_root.name}/'!")
    
    return catalog


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from VTT files and create structured Linux study guides."
    )
    parser.add_argument(
        "--subtitles-dir",
        type=str,
        default="linux subtitles",
        help="Path to root subtitles directory containing module folders (default: 'linux subtitles')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="linux_basics",
        help="Path to output directory for study guides (default: 'linux_basics')"
    )
    parser.add_argument(
        "--module",
        type=str,
        default=None,
        help="Optional specific module to process (e.g., 'working_with_shell')"
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent
    subtitles_path = (base_dir / args.subtitles_dir).resolve() if not Path(args.subtitles_dir).is_absolute() else Path(args.subtitles_dir)
    output_path = (base_dir / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    
    process_subtitles(subtitles_path, output_path, args.module)


if __name__ == "__main__":
    main()
