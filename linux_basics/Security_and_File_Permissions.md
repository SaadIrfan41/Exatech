# Security and File Permissions

How Linux decides **who** can do **what**: user accounts and groups, administrative privileges, file permissions, secure remote access, host firewalls and scheduled automation.

**Prerequisites:** *Working With Shell: Part 1 and 2* and *Linux Core Concepts* (especially `ls -l`, `sudo`, `/etc`, and file types).

> ⚠️ **Practice safely.** Many commands here create users, change permissions, edit firewall rules, or open remote access. Use a virtual machine, container or lab environment, not a machine you depend on. Firewall mistakes in particular can lock you out of a remote server.

---

## Table of Contents

1. [Why Access Control Matters](#1-why-access-control-matters)
2. [Account Types, UIDs and Groups](#2-account-types-uids-and-groups)
3. [Inspecting Users](#3-inspecting-users)
4. [Switching Users and `sudo`](#4-switching-users-and-sudo)
5. [Managing Users and Groups](#5-managing-users-and-groups)
6. [The Access Control Files](#6-the-access-control-files)
7. [File Permissions and Ownership](#7-file-permissions-and-ownership)
8. [Remote Access: SSH and SCP](#8-remote-access-ssh-and-scp)
9. [Host Firewalls with `iptables`](#9-host-firewalls-with-iptables)
10. [Scheduling Tasks with Cron](#10-scheduling-tasks-with-cron)
11. [Final Practice Lab](#11-final-practice-lab)
12. [Cheat Sheet](#12-cheat-sheet)

---

## 1. Why Access Control Matters

Imagine confidential customer data copied onto a company file share that **everyone** can read. Nobody hacked anything; permissions were simply too open. Routine security scans catch this kind of mistake, and it is exactly what the tools in this guide prevent.

Two ideas run through everything below:

- **Least privilege:** give each user and program only the access it needs, and nothing more.
- **Defence in depth:** use several layers together, so one mistake is not fatal:

| Layer | Tools in this guide |
| :--- | :--- |
| Who you are | User accounts, groups, passwords |
| What you may do | `sudo`, file permissions and ownership |
| How you connect | SSH keys |
| What traffic is allowed | `iptables` firewall |
| Automation and auditing | Cron, log files |

(Other layers exist, such as PAM, SELinux and firewalld, but are beyond this guide.)

---

## 2. Account Types, UIDs and Groups

Every user has an **account** holding a username, a password, and a unique numeric **UID**. A **group** is a collection of users with a unique **GID**, used to give several people the same access (for example, a `developers` group).

| Account type | UID | Purpose |
| :--- | :--- | :--- |
| **Superuser (root)** | `0` | Unrestricted control over everything |
| **System accounts** | Low numbers (typically below 1000) | Run OS components such as `sshd`; usually no login and no home in `/home` |
| **Service accounts** | Low numbers (typically below 1000) | Created when software is installed (for example `nginx`, `postgres`) so services don't run as root |
| **Regular users** | `1000` and up (older systems: 500+) | Real people, with a home directory and a login shell |

### Primary vs. supplementary groups

- Each user has exactly **one primary group**. By default it has the same name and number as the user.
- A user can also belong to any number of **supplementary groups** (`developers`, `docker`, `sudo`...), which grant shared access.

---

## 3. Inspecting Users

```bash
id               # your UID, primary GID, and all groups
id bob           # the same for another user
id -un           # just the username (same as whoami)
whoami           # effective username
who              # who is logged in right now
last -n 5        # the 5 most recent logins and reboots (from /var/log/wtmp)
```

Example `id` output:

```
uid=1001(michael) gid=1001(michael) groups=1001(michael),1005(developers)
```

---

## 4. Switching Users and `sudo`

### `su`: switch user

```bash
su bob           # become bob (asks for BOB's password); keeps your current environment
su - bob         # become bob with a full login environment (his home, PATH, profile)
su -             # become root (asks for ROOT's password)
su -c "ls /root" -    # run a single command as root
```

Using `su` means sharing the target account's password, which is not good practice, especially for root.

### `sudo`: run a command with elevated privileges

```bash
sudo systemctl restart nginx     # run one command as root
sudo -u postgres psql            # run as a specific user
sudo whoami                      # prints "root"
```

With `sudo`:

- You type **your own** password.
- Only users **listed** in the sudo policy can use it.
- You can be allowed **specific** commands only.
- Usage can be **logged** (on Debian/Ubuntu in `/var/log/auth.log`; on RHEL in `/var/log/secure`), giving an audit trail.

### The sudoers policy

The policy is in `/etc/sudoers`. **Always edit it with `visudo`**, which locks the file and checks the syntax before saving. A mistake in a hand-edited file can lock everyone out of `sudo`.

```bash
sudo visudo
```

Each rule has four fields:

```
WHO   WHERE=(RUN AS WHOM)   WHAT
bob   ALL=(ALL)             ALL
```

| Field | Meaning |
| :--- | :--- |
| 1. Who | A username, or a group prefixed with `%` (for example `%sudo`, `%wheel`) |
| 2. Where | The host(s) the rule applies to; normally `ALL` |
| 3. Run as | The user(s) they may become; normally `(ALL)` |
| 4. What | The command(s) allowed; `ALL` or specific absolute paths |

Examples:

```
bob    ALL=(ALL) ALL                      # full administrator
sara   ALL=(root) /sbin/shutdown -r now  # may ONLY run exactly this command
%developers ALL=(ALL) /usr/bin/systemctl restart nginx
# lines starting with # are comments
```

> If you wrote `sara ALL=(root) /sbin/shutdown` without arguments, Sara could run `shutdown` with **any** arguments, including powering the machine off. List the exact command line you want to allow.

Add a user to the admin group instead of editing the file: `sudo usermod -aG sudo bob` (Debian/Ubuntu) or `sudo usermod -aG wheel bob` (RHEL family).

### Disabling direct root login

Once `sudo` works for a trusted admin, you can stop anyone from logging in directly as root by giving root a non-login shell:

```bash
sudo usermod -s /sbin/nologin root
```

> ⚠️ Make sure at least one account can already use `sudo` before you do this. Some distros (such as Ubuntu) already have root's password locked by default.

---

## 5. Managing Users and Groups

All of these need root, so use `sudo`.

### Create a user: `useradd`

```bash
sudo useradd -m -s /bin/bash bob
sudo passwd bob                  # set the password
```

Always pass `-m` (create the home directory) and `-s` (shell) explicitly. Defaults differ between distros. On Debian/Ubuntu the plain command may not create a home directory and defaults to `/bin/sh`.

| Option | Meaning |
| :--- | :--- |
| `-m` | Create the home directory (copied from `/etc/skel`) |
| `-c "text"` | Comment (full name or description) |
| `-d /path` | Custom home directory |
| `-e YYYY-MM-DD` | Account expiry date |
| `-u UID` | Specific UID |
| `-g group` | Primary group (name or GID) |
| `-G g1,g2` | Supplementary groups |
| `-s shell` | Login shell (`/bin/bash`, `/sbin/nologin`...) |

Example with several options:

```bash
sudo groupadd -g 1009 avengers
sudo useradd -m -c "Bob Smith" -u 1500 -g avengers -G developers -s /bin/bash bob
id bob
```

(Debian/Ubuntu also have a friendlier interactive wrapper, `adduser`.)

### Passwords

```bash
sudo passwd bob          # set or change bob's password
passwd                   # change your own
sudo passwd -l bob       # lock the account password
sudo passwd -u bob       # unlock
sudo chage -l bob        # show password aging details
```

### Change a user: `usermod`

```bash
sudo usermod -aG developers bob     # ADD bob to a supplementary group
sudo usermod -s /bin/zsh bob        # change shell
```

> ⚠️ **Always use `-a` together with `-G`.** `usermod -G developers bob` (without `-a`) **replaces** all of bob's supplementary groups with just `developers`. Group changes apply at the user's **next login**.

### Delete a user or group

```bash
sudo userdel bob          # remove the account, keep the home directory
sudo userdel -r bob       # also remove home directory and mail
sudo groupadd developers
sudo groupadd -g 2001 testers    # with a specific GID
sudo groupdel developers         # cannot delete some user's primary group
```

---

## 6. The Access Control Files

These files in `/etc` define accounts. Anyone can read some of them, but only root can change them. **Don't edit them in a normal text editor.** Use the commands above, or `vipw` / `vigr` if you must edit by hand (they lock the file to prevent corruption).

### `/etc/passwd`: user accounts (7 fields, separated by `:`)

```
bob:x:1001:1001:Bob Smith:/home/bob:/bin/bash
 1  2   3    4       5         6         7
```

| # | Field | Meaning |
| :--- | :--- | :--- |
| 1 | Username | Login name |
| 2 | Password | `x` means "the hash is in `/etc/shadow`" |
| 3 | UID | User ID |
| 4 | GID | Primary group ID |
| 5 | GECOS | Comment, usually the full name (optional) |
| 6 | Home | Home directory path |
| 7 | Shell | Login shell (`/sbin/nologin` or `/usr/sbin/nologin` = no interactive login) |

Despite the name, it contains **no passwords**. It is world-readable (`644`) because many programs need to map UIDs to names.

### `/etc/shadow`: password hashes and aging (9 fields)

Readable only by root (and on some systems the `shadow` group).

```
bob:$6$salt$hash...:19700:0:99999:7:::
```

| # | Field | Meaning |
| :--- | :--- | :--- |
| 1 | Username | Same as in `passwd` |
| 2 | Password hash | A salted hash (for example `$6$` = SHA-512; newer systems may use `$y$` = yescrypt). `!` or `*` = **no password login possible**. An **empty** field = **no password required** (dangerous) |
| 3 | Last changed | Days since 1 Jan 1970 (the "epoch") |
| 4 | Minimum age | Days before the password may be changed again |
| 5 | Maximum age | Days before the password must be changed |
| 6 | Warning | Days of warning before it expires |
| 7 | Inactive | Days after expiry before the account is disabled |
| 8 | Expiry | Account expiry date (epoch days) |
| 9 | Reserved | Unused |

Empty fields mean "not enforced."

### `/etc/group`: groups (4 fields)

```
developers:x:1005:bob,michael
    1      2   3      4
```

Group name, password placeholder (`x`), GID, and a comma-separated member list. (It lists *supplementary* members. Users whose primary group this is may not appear in field 4.)

### Handy queries

```bash
getent passwd bob        # look up a user (also works for network directories like LDAP)
getent group developers  # look up a group
grep "^$USER:" /etc/passwd
sudo chage -l bob        # readable view of the password aging fields
```

---

## 7. File Permissions and Ownership

### Reading `ls -l`

```
-rwxr-xr--  1  bob  developers  1204  Oct 1 10:00  deploy.sh
│└┬┘└┬┘└┬┘     │       │
│ │  │  │      │       └── owning group
│ │  │  │      └────────── owning user
│ │  │  └── others (o)
│ │  └───── group (g)
│ └──────── owner / user (u)
└────────── file type (- file, d directory, l link ...)
```

Every file has an **owner** and a **group**, and three sets of permissions:

| Class | Applies to |
| :--- | :--- |
| `u` (user/owner) | The file's owner |
| `g` (group) | Members of the file's group |
| `o` (others) | Everyone else |

### What `r`, `w`, `x` mean

| | On a **file** | On a **directory** |
| :--- | :--- | :--- |
| `r` (read) | View the contents | **List** the names inside (`ls`) |
| `w` (write) | Modify the contents | **Create, delete and rename** files inside (needs `x` too) |
| `x` (execute) | Run it as a program or script | **Enter** it (`cd`) and access items inside by name |

Without `x` on a directory you cannot get to the files inside, even if the files themselves are readable.

### Who is checked: owner, then group, then others

Linux checks **in order and stops at the first match**:

1. If you are the **owner**, only the owner's permissions apply.
2. Otherwise, if you are in the file's **group**, only the group's permissions apply.
3. Otherwise, the **others** permissions apply.

So an owner with *fewer* rights than the group is still restricted to the owner's rights. For example, on a directory with mode `d--xrwxrwx` owned by bob, Bob can `cd` in but gets "Permission denied" listing it, even though everyone else can. (The root user bypasses these checks.)

### Octal notation

Each permission has a value; add them for each class:

| Permission | Value |
| :--- | :--- |
| `r` | 4 |
| `w` | 2 |
| `x` | 1 |
| none | 0 |

| `rwx` | `rw-` | `r-x` | `r--` | `-wx` | `--x` | `---` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 7 | 6 | 5 | 4 | 3 | 1 | 0 |

A mode is three digits: owner, group, others.

| Mode | Meaning | Typical use |
| :--- | :--- | :--- |
| `755` | `rwxr-xr-x` | Programs, scripts, public directories |
| `644` | `rw-r--r--` | Normal files |
| `700` | `rwx------` | Private directory |
| `600` | `rw-------` | Private file (SSH keys, secrets) |
| `750` | `rwxr-x---` | Owner full, group read/enter, others nothing |
| `660` | `rw-rw----` | Owner and group read/write, others nothing |
| `777` | `rwxrwxrwx` | ⚠️ Everyone can do everything. Almost never the right answer |

### Changing permissions: `chmod`

**Numeric (octal) mode:**

```bash
chmod 755 script.sh
chmod 600 secret.txt
chmod -R 750 /opt/project      # -R = recursive (use carefully)
```

**Symbolic mode:** `chmod [who][+|-|=][permissions]`, where *who* is `u`, `g`, `o`, or `a` (all).

```bash
chmod u+x script.sh        # give the owner execute
chmod g-w file.txt         # remove write from the group
chmod o= file.txt          # set others to no permissions
chmod u+rwx,g+rx,o-rwx f   # several changes at once
chmod a+r notes.txt        # everyone can read
```

### Changing owner and group: `chown`, `chgrp`

```bash
sudo chown bob app.py                # change owner
sudo chown bob:developers app.py     # change owner and group
sudo chown :developers app.py        # change only the group
sudo chown -R bob /opt/myapp         # recursive
sudo chgrp developers app.py         # change group only
```

Only root can change a file's owner. The owner can change the group, but only to a group they belong to.

### Default permissions: `umask`

New files start from `666` (files) and `777` (directories), minus the **umask**.

```bash
umask          # e.g. 0022  ->  new files 644, new directories 755
umask 027      # new files 640, new directories 750 (current shell only)
```

### Fixing the "confidential file on a shared folder" problem

```bash
ls -ld /shared/client_data              # inspect the directory itself
sudo chgrp finance /shared/client_data  # restrict to a specific group
sudo chmod 770 /shared/client_data      # owner + group only, others nothing
sudo chmod -R o-rwx /shared/client_data # remove all access for others from everything inside
```

---

## 8. Remote Access: SSH and SCP

**SSH** (Secure Shell) gives you an encrypted command-line session on a remote machine. It replaced unencrypted tools like `telnet` and `rsh`. The server runs the `sshd` service, listening on **TCP port 22** by default.

### Connecting

```bash
ssh devapp01                # log in as your current username
ssh bob@devapp01            # log in as bob
ssh -l bob devapp01         # same, using the -l option (lowercase L)
ssh -p 2222 bob@10.0.0.5    # non-standard port
ssh bob@devapp01 uptime     # run one command remotely and return
```

(Capital `-L` is something different: port forwarding.) You need a valid account on the remote machine, and port 22 must be reachable. The first time you connect to a server, SSH shows its **fingerprint** and asks you to confirm; it is then remembered in `~/.ssh/known_hosts`.

### Key-based authentication (password-less login)

Instead of a password, you can use a **key pair**:

| Key | Default file | Rule |
| :--- | :--- | :--- |
| **Private key** | `~/.ssh/id_ed25519` (or `id_rsa`) | Stays on **your** machine. **Never share it.** Must be mode `600`. |
| **Public key** | `~/.ssh/id_ed25519.pub` | Safe to share. Copied to servers you want to access. |

The server holds your public key; only the holder of the matching private key can prove their identity.

```bash
ssh-keygen -t ed25519                  # generate a key pair (modern default choice)
ssh-keygen -t rsa -b 4096              # RSA alternative, still widely used
ssh-copy-id bob@devapp01               # install your public key (asks for password once)
ssh bob@devapp01                       # now logs in without a password
```

- `ssh-keygen` asks for an optional **passphrase**. It protects the key if someone steals the file, at the cost of typing it when you use the key (an *ssh-agent* can remember it).
- `ssh-copy-id` appends your public key to `~/.ssh/authorized_keys` on the server.
- SSH is strict about permissions: `~/.ssh` should be `700`, and the private key and `authorized_keys` should be `600`.

### Copying files: `scp`

`scp` copies files over SSH, like `cp` across machines.

```bash
scp app.tar.gz bob@devapp01:~/              # local -> remote home directory
scp bob@devapp01:/var/log/app.log .         # remote -> here
scp -r project/ bob@devapp01:/opt/          # -r copies directories
scp -p file.txt bob@devapp01:~/             # -p preserves times and modes
scp -P 2222 file.txt bob@devapp01:~/        # NOTE: capital -P for port in scp
```

The part after the colon is the destination path. You need write permission there, or you will get "Permission denied." For big or repeated transfers, `rsync -av` over SSH is often better.

---

## 9. Host Firewalls with `iptables`

Networks are usually protected by perimeter firewalls (Cisco, Fortinet and others). A **host firewall** also protects each individual server, which limits the damage if something else on the network is compromised. Linux's packet filter is **Netfilter**, managed with `iptables` (newer systems also offer `nftables`, `firewalld` and `ufw` front-ends). All `iptables` commands need root.

### Chains and policies

Rules are grouped into **chains** in the `filter` table:

| Chain | Packets that... |
| :--- | :--- |
| `INPUT` | arrive **at** this host |
| `OUTPUT` | are **created by** this host and leave it |
| `FORWARD` | pass **through** this host to somewhere else (routers) |

Each chain has a **default policy** (`ACCEPT` or `DROP`) used when no rule matches. Out of the box it is `ACCEPT` everywhere, meaning everything is allowed.

### How rules are evaluated

A chain is a **list of rules checked from top to bottom**. The **first rule that matches** decides the packet's fate (`ACCEPT`, `DROP` or `REJECT`) and the rest are ignored. If nothing matches, the policy applies. **Order is everything.**

### Rule anatomy

```bash
sudo iptables -A INPUT -p tcp -s 172.16.238.187 --dport 22 -j ACCEPT
```

| Part | Meaning |
| :--- | :--- |
| `-A INPUT` | **A**ppend to the end of the `INPUT` chain |
| `-p tcp` | Protocol (`tcp`, `udp`, `icmp`) |
| `-s 172.16.238.187` | Source address or network (e.g. `10.0.0.0/24`) |
| `-d <ip>` | Destination address |
| `--dport 22` | Destination port |
| `-j ACCEPT` | Jump to target: `ACCEPT`, `DROP` (silently discard; the sender waits and times out) or `REJECT` (discard and notify the sender immediately) |

### Listing and deleting

```bash
sudo iptables -L                        # list all chains
sudo iptables -L -n -v                  # numeric addresses, with packet counters
sudo iptables -L INPUT --line-numbers   # numbered rules
sudo iptables -S                        # rules as commands, plus policies
sudo iptables -D OUTPUT 5               # delete rule number 5 in OUTPUT
sudo iptables -I INPUT 1 <rule...>      # INSERT at position 1 (top)
sudo iptables -P FORWARD DROP           # change a default policy
sudo iptables -F                        # flush (delete) all rules
```

> ⚠️ **Don't lock yourself out.** On a remote server, add the `ACCEPT` rule for your own SSH connection **before** any rule or policy that blocks SSH. Test from a second session. `iptables -F` removes your protections (and with a `DROP` policy can cut your connection).
>
> After deleting a rule, the numbers below it shift, so list again before deleting another.

### Worked example: a small dev environment

Hosts: client laptop `172.16.238.187`, app server `172.16.238.10`, database server `172.16.238.11`.

**Requirements**

- Only the laptop may SSH to the app server and reach its web app on port 80.
- The app server may connect to the database (port 5432) and to the internal software repository (HTTP).
- The app server may not reach the internet directly.
- The database accepts port 5432 **only** from the app server.

**On the app server**

```bash
# INPUT: allow the laptop first, then block everyone else
sudo iptables -A INPUT -p tcp -s 172.16.238.187 --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j REJECT
sudo iptables -A INPUT -p tcp -s 172.16.238.187 --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j REJECT

# OUTPUT: allow the database and the repository, block web access elsewhere
sudo iptables -A OUTPUT -p tcp -d 172.16.238.11 --dport 5432 -j ACCEPT
sudo iptables -A OUTPUT -p tcp -d <repo-ip> --dport 80 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 80 -j REJECT
sudo iptables -A OUTPUT -p tcp --dport 443 -j REJECT
```

**On the database server**

```bash
sudo iptables -A INPUT -p tcp -s 172.16.238.10 --dport 5432 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5432 -j REJECT
```

**An exception that must go on top.** Suppose the app server also needs HTTPS to one trusted site. An `ACCEPT` appended at the end would never be reached, because the `REJECT` for port 443 matches first. **Insert** it at the top instead:

```bash
sudo iptables -I OUTPUT 1 -p tcp -d <trusted-ip> --dport 443 -j ACCEPT
```

### Replies and ephemeral ports

When the app server connects *out* to port 5432, its own side uses a random temporary (**ephemeral**) port, typically 32768–60999. The database's reply comes back to that port. In the example above this works only because the app server's INPUT rules block just ports 22 and 80, so the reply is not caught. On a stricter host with a `DROP` policy you must allow replies explicitly using connection tracking:

```bash
sudo iptables -I INPUT 1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -I INPUT 2 -i lo -j ACCEPT        # allow loopback traffic
```

### Check before you filter

```bash
ss -tuln                 # which ports are listening (modern replacement for netstat)
ss -tn | grep 5432       # active connections to a port, with ephemeral source ports
```

### Rules are not permanent

`iptables` rules live in memory and **vanish on reboot**. To keep them, save them with your distro's mechanism (for example `iptables-save`, the `iptables-persistent`/`netfilter-persistent` package on Debian/Ubuntu, or the `iptables-services` package on RHEL-family systems).

---

## 10. Scheduling Tasks with Cron

**Cron** runs commands automatically at times you choose. The `cron` (or `crond`) service wakes every minute, checks the schedules, and runs whatever is due. Each user has a personal **crontab**.

```bash
crontab -e       # edit YOUR crontab (opens in $EDITOR, often vi)
crontab -l       # list your jobs
crontab -r       # delete ALL your jobs (no confirmation!)
sudo crontab -u bob -l    # view another user's crontab
```

> Don't run `sudo crontab -e` unless you mean to edit **root's** crontab. Run it as the user who should own the job.

### The schedule: 5 time fields + the command

```
┌───────── minute        (0–59)
│ ┌─────── hour          (0–23)
│ │ ┌───── day of month  (1–31)
│ │ │ ┌─── month         (1–12)
│ │ │ │ ┌─ day of week   (0–7; 0 and 7 = Sunday)
│ │ │ │ │
* * * * *  command to run
```

| Symbol | Meaning | Example |
| :--- | :--- | :--- |
| `*` | Every value | `* * * * *` = every minute |
| `,` | A list | `0 8,12,18 * * *` = 8:00, 12:00 and 18:00 daily |
| `-` | A range | `0 9 * * 1-5` = 9:00 on weekdays |
| `/n` | Every nth | `*/5 * * * *` = every 5 minutes; `*/2 * * * *` = every 2 minutes |

More examples:

```cron
0 21 * * *      /usr/bin/uptime >> /tmp/system-report.txt 2>&1   # 9:00 PM every day
10 8 19 2 *     /home/bob/yearly.sh                               # 8:10 AM on 19 February
30 2 * * 0      /home/bob/backup.sh                               # 2:30 AM every Sunday
@reboot         /home/bob/start.sh                                # at boot
@daily          /home/bob/cleanup.sh                              # once a day
```

> ⚠️ **Day-of-month and day-of-week are combined with OR, not AND.** `10 8 19 2 1` runs at 8:10 on **February 19th *and also* on every Monday in February**, not only when the 19th is a Monday. If you need an AND, test the weekday inside the script.

### Cron pitfalls

1. **Use absolute paths.** Cron runs with a minimal environment and a short `PATH`. Write `/usr/bin/python3`, not `python3`. Find paths with `which`.
2. **Capture output and errors.** Add `>> /path/to/job.log 2>&1`. Otherwise output is mailed to the user, or lost. Use `>>` (append) rather than `>`, which overwrites the log every run.
3. **Escape `%`.** In a crontab line, `%` is special and must be written `\%` (for example in `date +\%F`).
4. **Test the command by hand first**, in the same user's shell.

### Checking that jobs ran

```bash
grep CRON /var/log/syslog | tail -n 10      # Debian/Ubuntu
sudo grep CRON /var/log/cron | tail -n 10   # RHEL family
journalctl -u cron                          # systemd (service is "crond" on RHEL family)
```

### System-wide schedules

`/etc/crontab` and files in `/etc/cron.d/` use the same format **plus a username column** before the command. The directories `/etc/cron.hourly`, `.daily`, `.weekly` and `.monthly` hold scripts that run on those schedules.

---

## 11. Final Practice Lab

Use a disposable VM or container. Anything that creates users, changes firewall rules, or touches system files should not be run on a machine you rely on.

**Part A: Identify yourself**

1. Run `id`, `whoami`, `who` and `last -n 5`.
2. Run `grep "^$USER:" /etc/passwd` and label all 7 fields.
3. Run `grep "^$USER:" /etc/group`, then `sudo chage -l $USER`.
4. Confirm `sudo whoami` prints `root`.

**Part B: Users and groups**

5. `sudo groupadd testdevs`
6. `sudo useradd -m -s /bin/bash -c "Dev Account" -G testdevs devbob`
7. `id devbob`, then `getent passwd devbob`.
8. `sudo passwd devbob`
9. Create a second group, then add devbob without losing the first: `sudo groupadd testops && sudo usermod -aG testops devbob`, then `id devbob`.
10. `su - devbob`, run `whoami` and `pwd`, then `exit`.
11. Clean up: `sudo userdel -r devbob && sudo groupdel testdevs && sudo groupdel testops`

**Part C: Permissions**

12. `touch test_perms.txt` and check it with `ls -l`.
13. `chmod 600 test_perms.txt`, then `chmod u+x test_perms.txt`, checking after each.
14. Make a script runnable: `echo 'echo Hello' > run.sh && chmod 755 run.sh && ./run.sh`
15. Remove the execute bit (`chmod 644 run.sh`) and try running it again. What error do you get?
16. Run `umask`, create a new file and directory, and compare their modes with the umask rule.
17. Create a shared directory: `mkdir shared && sudo groupadd team && sudo chgrp team shared && chmod 770 shared`, then `ls -ld shared`.
18. Directory `x` experiment: `mkdir d && touch d/f && chmod 644 d` then try `ls d` and `cat d/f`. Then `chmod 711 d` and try again. Explain the difference. Clean up with `chmod 755 d` and `rm -r d`.
19. Clean up: `rm -rf test_perms.txt run.sh shared && sudo groupdel team`

**Part D: SSH keys (local only)**

20. `ls -la ~/.ssh`
21. `ssh-keygen -t ed25519 -f /tmp/test_key -N ""`
22. `ls -l /tmp/test_key*`. Which file is `600`? Why?
23. `cat /tmp/test_key.pub`, then clean up with `rm /tmp/test_key*`.

**Part E: Firewall (safe local test)**

24. Start a test web server: `python3 -m http.server 8080 &` and check it with `curl -sI localhost:8080`.
25. Block it: `sudo iptables -A INPUT -p tcp --dport 8080 -j REJECT`, then repeat `curl`. It should fail.
26. `sudo iptables -L INPUT -n --line-numbers`, then delete the rule: `sudo iptables -D INPUT <number>`.
27. Confirm `curl` works again, then stop the server with `kill %1`.

**Part F: Cron**

28. Add a test job:
    ```bash
    (crontab -l 2>/dev/null; echo '*/2 * * * * /usr/bin/date >> /tmp/cron_test.log 2>&1') | crontab -
    ```
29. `crontab -l`, wait a few minutes, then `cat /tmp/cron_test.log`.
30. Find the entries in the cron log (see section 10), then clean up with `crontab -r` and `rm /tmp/cron_test.log`.

---

## 12. Cheat Sheet

| Command | Purpose |
| :--- | :--- |
| `id [user]` / `whoami` / `who` / `last` | Who am I, who is logged in, login history |
| `su - user` / `sudo cmd` | Switch user / run with privileges |
| `sudo visudo` | Safely edit sudo policy |
| `useradd -m -s /bin/bash user` | Create a user |
| `passwd [user]` / `passwd -l` / `-u` | Set password / lock / unlock |
| `usermod -aG group user` | Add to a group (**always `-a`**) |
| `userdel -r user` | Delete user and home |
| `groupadd` / `groupdel` | Create / delete group |
| `getent passwd\|group name` | Look up accounts |
| `chage -l user` | Password aging |
| `/etc/passwd` `/etc/shadow` `/etc/group` | Account databases |
| `ls -l` / `ls -ld dir` | Show permissions |
| `chmod 755 f` / `chmod u+x f` | Change permissions (octal / symbolic) |
| `chown user:group f` / `chgrp group f` | Change owner / group |
| `umask` | Default permission mask |
| `ssh [user@]host` | Remote login |
| `ssh-keygen -t ed25519` / `ssh-copy-id user@host` | Create / install a key |
| `scp [-r -p -P port] src dest` | Copy over SSH |
| `iptables -L -n --line-numbers` | List firewall rules |
| `iptables -A\|-I CHAIN ... -j ACCEPT\|DROP\|REJECT` | Append / insert a rule |
| `iptables -D CHAIN n` / `-P CHAIN POLICY` | Delete a rule / set policy |
| `ss -tuln` | Listening ports |
| `crontab -e` / `-l` / `-r` | Edit / list / remove your cron jobs |
| `m h dom mon dow command` | Cron schedule format |

**Permission quick reference:** `r=4 w=2 x=1`. Owner, then group, then others. First match wins, and root bypasses all of it.