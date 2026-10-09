# Linux Commands & Vim: Beginner Guide

This guide covers the core Linux terminal commands and the Vim text editor — the everyday tools you'll use constantly once you start working with servers, containers, and cloud machines.

**A note before we start:** everything you type into the terminal is called a **command**. You type it, press Enter, and the computer does exactly what you asked — nothing more, nothing less.

---

## Module 1: Finding your way around

### `pwd` — "Where am I?"
Prints the exact folder you're currently standing in.

```bash
pwd
# Output: /home/user/documents
```

### `cd` — "Go somewhere else"
Moves you into a different folder.

```bash
cd /var/log      # Go to a specific folder (by its full path)
cd ..             # Go up one folder (to the parent)
cd ~              # Jump straight back to your home folder
```

### `date` — "What's the date/time right now?"
Shows the computer's current date and time.

```bash
date
```

### `clear` — "Wipe the screen"
Clears everything currently shown in the terminal, so you start with a clean screen. It doesn't delete anything — just tidies up what you can *see*.

```bash
clear
```

---

## Module 2: Working with files and folders

### `ls` — "What's in this folder?"
Lists everything inside your current folder.

```bash
ls              # Simple list
ls -ltr         # A more detailed list, newest files at the bottom
```

- `-l` = show details (size, date, who owns it)
- `-t` = sort by time changed
- `-r` = reverse the order (newest at the bottom instead of the top)

### `mkdir` / `rmdir` — "Make a folder" / "Remove an empty folder"

```bash
mkdir project_files      # Creates a new folder
rmdir empty_folder       # Deletes a folder — only works if it's empty
```

### `touch` — "Create a blank file"
Makes a brand-new, empty file instantly — no need to open an editor first.

```bash
touch notes.txt
```

### `cp` — "Copy"
Makes a duplicate of a file or folder, leaving the original where it was.

```bash
cp source.txt destination.txt        # Copy one file
cp -r folder1/ folder1_backup/       # Copy a whole folder (-r = "and everything inside it")
```

### `mv` — "Move or rename"
Moves a file somewhere else — or, if you give it a new name in the same folder, it renames the file instead.

```bash
mv file.txt /tmp/               # Move file.txt into the /tmp folder
mv old_name.txt new_name.txt    # Rename a file
```

### `rm` — "Delete, permanently"
Removes a file or folder for good — there's no trash bin to recover it from, so use carefully.

```bash
rm file.txt          # Delete a single file
rm -r my_folder/     # Delete a folder and everything inside it (-r = "and everything inside it")
```

---

## Module 3: Reading and writing file content

### `cat` — "Print the whole file"
Shows a file's full content right in the terminal.

```bash
cat /etc/resolv.conf
```

### `head` — "Show me just the start"
Shows the first lines of a file (10 by default).

```bash
head file.txt         # First 10 lines
head -n 5 file.txt     # First 5 lines
```

### `tail` — "Show me just the end"
Shows the last lines of a file.

```bash
tail -n 5 file.txt        # Last 5 lines
tail -f /var/log/syslog    # Keep watching the file live, as new lines get added
```
`-f` ("follow") is especially useful for watching a running app's logs update in real time.

### `echo` and `>` — "Print text, or save it into a file"

```bash
echo "hello world"                  # Just prints text to the screen
echo "hello world" > filename.txt    # Overwrites filename.txt with "hello world"
echo "new entry" >> filename.txt     # Adds a new line WITHOUT deleting what's already there
```
One `>` replaces the file's content. Two `>>` adds to the end without erasing anything.

---

## Module 4: Shortcuts and background tasks

### `ln -s` — "Create a shortcut to a file"
Makes a shortcut (called a **symbolic link**) that points to another file, without actually duplicating it.

```bash
ln -s /path/to/original.txt shortcut.txt
```
Opening `shortcut.txt` behaves exactly like opening the original — but if the original file ever gets deleted, the shortcut stops working (it's just pointing at something that's no longer there).

### `nohup` — "Keep running even after I close the terminal"
Normally, if you close your terminal, anything you were running stops too. `nohup` keeps a program running in the background even after you disconnect.

```bash
nohup python3 script.py &
```
The `&` at the end also matters — it tells the terminal *"run this in the background, and give me my terminal back immediately"* instead of waiting for it to finish. You'll use this pattern a lot once you're starting long-running programs or servers on a remote machine.

---

## Module 5: Checking your system's health

### `free -h` — "How much memory (RAM) is free?"

```bash
free -h
```
`-h` means "human-readable" — it shows sizes like `2.1GB` instead of a huge number of raw bytes.

### `df -h` — "How much disk space is free?"

```bash
df -h
```
Useful for spotting when a server's storage is nearly full — a very common real-world troubleshooting task.

---

## Module 6: Vim — the text editor

Vim opens and edits files without leaving the terminal. Unlike most text editors, Vim has different **modes** — you're either navigating/giving commands, or actively typing text, never both at once.

```bash
vim filename.txt     # Opens (or creates) filename.txt in Vim
```

| Key / Command | What it does |
|---|---|
| `i` | Start typing (enters **Insert Mode**) |
| `Esc` | Stop typing, go back to giving commands (**Normal Mode**) |
| `:w` | Save the file (without closing) |
| `:q` | Close Vim (only works if there's nothing unsaved) |
| `:q!` | Close Vim immediately, throwing away any unsaved changes |
| `:wq` | Save AND close, in one step |
| `u` | Undo the last change |
| `Ctrl + r` | Redo (undo the undo) |
| `yy` | Copy the current line |
| `p` | Paste below the current line |
| `P` | Paste above the current line |
| `dd` | Delete (cut) the current line |
| `dw` | Delete the rest of the current word |
| `v` | Start selecting text (**Visual Mode**) — move with arrow keys, then press `y` to copy the selection |

**The one thing to burn into memory as a beginner:** if you're ever stuck in Vim and don't know what mode you're in, press `Esc` a couple of times to get back to Normal Mode, then type `:q!` and Enter to escape without saving anything.

---

## Where things live on a Linux system

A quick map for later, once you start working with real servers:

| Folder | What's usually there |
|---|---|
| `/bin` | Everyday commands everyone can use (`ls`, `cp`, `cat`, `mkdir`, `rm`) |
| `/sbin` | Admin-only commands (`fdisk`, `ifconfig`, `reboot`) |
| `/etc` | Configuration files — often edited directly with `vim` |
| `/var/log` | Log files — the usual target for `tail -f` |
| `/tmp` | Temporary scratch space; safe to clean out |

---

# Class Project: Terminal Treasure Hunt

A hands-on lab that uses almost every command above. Students build a small "treasure hunt" folder structure themselves, hide a prize deep inside it, then use the commands to navigate to it, read clues, and "claim" the treasure by editing a file in Vim.

## The setup

Have students run this in a fresh folder to build the hunt (or build it yourself and hand it to them as a starting point — either works):

```bash
mkdir -p treasure_hunt/forest/cave/chest
cd treasure_hunt
echo "Welcome, explorer. Your first clue is inside the forest." > start_here.txt
echo "Deeper in... check the cave." > forest/clue1.txt
echo "You're close. Look inside the chest." > forest/cave/clue2.txt
echo "TREASURE: the secret word is PINEAPPLE" > forest/cave/chest/treasure.txt
touch forest/cave/decoy1.txt forest/cave/decoy2.txt
```

## The challenge (give this part to students)

1. **Find out where you are.** Use `pwd` to confirm you're inside `treasure_hunt`.
2. **Read the first clue.** Use `cat start_here.txt`.
3. **Move into the forest.** Use `cd forest`, then `ls` to see what's there.
4. **Read the next clue** with `cat clue1.txt`, and follow it into the cave.
5. **Spot the real clue among decoys.** The `cave` folder has some decoy files mixed in. Use `ls -ltr` — the real clue (`clue2.txt`) was created *before* the decoys, so it won't be the most recent file. Use `head` or `cat` on a couple of files to figure out which one is real.
6. **Reach the chest** and read `treasure.txt` to find the secret word.
7. **Claim the treasure.** Create a file called `claimed_by.txt` using `touch`, then open it with `vim`, type your name and the secret word, save, and quit (`:wq`).
8. **Make a shortcut.** Back in the `treasure_hunt` folder, use `ln -s` to create a shortcut called `my_treasure` that points directly at `forest/cave/chest/treasure.txt` — so next time, you can `cat my_treasure` instead of navigating the whole path again.
9. **Back up your win.** Use `cp` to copy `claimed_by.txt` into a new folder called `trophies/` (you'll need `mkdir` first).
10. **Clean up the decoys.** Use `rm` to delete the two decoy files in the cave.
11. **Final system check.** Before you celebrate, check that your "server" (your machine) can handle more treasure hunting: run `free -h` and `df -h` and note down how much memory and disk space are free.

**Bonus round (for students who finish early):**
Start a countdown using `nohup`:
```bash
nohup bash -c 'for i in 5 4 3 2 1; do echo "Launching in $i..." >> countdown.log; sleep 1; done; echo "🎉 Treasure secured!" >> countdown.log' &
```
Then use `tail -f countdown.log` to watch it live, right up to the final celebration message. Press `Ctrl + C` to stop watching once it's done (this doesn't stop the countdown itself — just stops you watching it).

## What this reinforces

| Command practiced | Where |
|---|---|
| `pwd`, `cd`, `ls`, `ls -ltr` | Navigating the hunt |
| `cat`, `head` | Reading clues, spotting the real file among decoys |
| `mkdir`, `touch` | Setting up folders and claim files |
| `vim` (`i`, `Esc`, `:wq`) | Claiming the treasure |
| `ln -s` | Creating a shortcut to the treasure |
| `cp`, `rm` | Backing up your win, cleaning up decoys |
| `free -h`, `df -h` | Final system check |
| `nohup`, `tail -f`, `&` | Bonus round background countdown |