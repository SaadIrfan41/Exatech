# Student Handout: Design Cases and Practices of an O&M Solution

## 1. What this lab is about

In this lab you take a working website, Discuz! (a forum application), and turn it into a service that can be run and supported. Its web server already runs, but it is not connected to a database yet. You will:

1. Put the database in its own private network.
2. Connect the web server to a managed database (RDS).
3. Watch the server with Cloud Eye and get an email when it restarts.
4. Collect logs with LTS and get an email when a keyword ("Stopped") appears.
5. Break something on purpose and confirm the alarm reaches your inbox.

**ShopFast example:** ShopFast's checkout works, but nobody is told when it fails. This lab adds the three things a real team needs: a private database, monitoring, and alerts.

| Stage | ShopFast equivalent | Lab section |
|---|---|---|
| Private database network | Customer orders stay away from the public internet | Section 2, steps 1–2 |
| Managed database | Checkout reads and writes orders in RDS | Section 2, steps 3–4 |
| Metrics and events | Know when a server is struggling or restarts | Section 3 |
| Email alert | The on-call engineer is emailed at 02:00 | Section 3, step 2 |
| Logs | Find why checkout failed at 19:20 | Section 4, steps 1–3 |
| Keyword alarm | Email when the service logs "Stopped" | Section 4, step 4 |

**Learning objectives**

1. Build a network-separated database and connect it to a web application.
2. Restrict access so only the web server can reach the database.
3. Monitor a server with Cloud Eye and send alerts through SMN.
4. Collect logs with LTS and create a keyword alarm.
5. Trigger a failure on purpose and confirm the alarm arrives.

---

## 2. Key terms used in this lab

- **VPC:** your private network in the cloud. Everything in this lab lives inside one VPC.
- **Subnet:** a smaller address range inside the VPC. A subnet sits in one Availability Zone (AZ). For example, 192.168.2.0/24 gives 256 addresses, and 5 are reserved by the cloud, so 251 are usable.
- **Private IP:** an address that only works inside your VPC (for example 192.168.2.10). The internet cannot reach it directly.
- **Security group (SG):** a firewall attached to a server. It lists which traffic is allowed: the port, the protocol and the source. It is stateful, so a reply to an allowed request goes back out automatically.
- **Source (in a security group rule):** where the traffic is allowed to come from. `0.0.0.0/0` means "anyone on the internet". A single private IP or a security group means "only that machine or group".
- **RDS:** a managed database. The cloud handles backups, patching and failover for you.
- **Primary / standby:** the primary takes reads and writes. The standby is a copy in another AZ that takes over if the primary's AZ fails.
- **Cloud Eye:** the monitoring service. It collects metrics (CPU, memory, disk) and events (such as a reboot).
- **SMN:** the notification service. It sends messages to email subscribers.
- **LTS:** the log service. It stores logs, lets you search them and can alarm on them.
- **ICAgent:** the agent installed on a server that sends its logs to LTS. It is not the same as the Cloud Eye agent.
- **AK/SK:** an Access Key and Secret Key. Together they act like a username and password for your cloud account.

---

## 3. Before you start

- Log in with the lab credentials. Do not use your own cloud account for the lab.
- Keep the AK/SK private. Never paste it into chat, a shared document or a public repository.
- Note the **private IP of ecs-web**. You need it in Section 2, step 2.
- Note the **RDS private IP and password**. You need them in Section 2, step 4.

---

## 4. Section by section

### Section 1: Preset environment and login

**What you do:** Log in with the lab account. The VPC, the web server (ecs-web) and Discuz! are already created.

**Why:** Lab resources are created and cleaned up automatically. A personal account could be left with charges or broken settings.

**Example:** This is the same as getting a test copy of a shop's checkout system instead of working on the live one.

---

### Section 2, Step 1: Create subnet-db (192.168.2.0/24)

**What you do:** In the existing VPC, create a new subnet named `subnet-db` with the range 192.168.2.0/24.

**Why:** The web server and the database should not share a network. If an attacker breaks into the web server, they still have to get past a second boundary to reach the database.

**Example:** ShopFast puts the web servers in one subnet and the orders database in another. The database subnet has no route to the internet.

---

### Section 2, Step 2: Create sg-db and set the source to ecs-web

**What you do:**
- Create a security group named `sg-db`.
- Add one inbound rule: protocol TCP, port **3306** (MySQL), source = the **private IP of ecs-web** (for example `192.168.1.25/32`).
- Do not use `0.0.0.0/0` as the source.

**What the rule means, in plain words:** "Allow MySQL connections to the database, but only if they come from the web server's address." Every other address is blocked.

**Example:**

| Source | Port | Result |
|---|---|---|
| 192.168.1.25/32 (ecs-web) | 3306 | Allowed |
| 0.0.0.0/0 (anyone) | 3306 | Not allowed by this lab's design; a real database must never be open to everyone |
| 203.0.113.50/32 (an attacker) | 3306 | Blocked, because it is not in the rule |

**Why the `/32`:** `/32` means one exact address. Without it, you would be allowing a whole range.

**Warning about sg-web in this lab:** the lab opens SSH (port 22) to `0.0.0.0/0` for the web server. This is convenient for a lab, but in production you would allow SSH only from your own office IP, for example `203.0.113.10/32`.

---

### Section 2, Step 3: Buy an RDS database (MySQL 5.7, primary/standby)

**What you do:** Create an RDS MySQL 5.7 instance in `subnet-db` with `sg-db`, deployed as primary/standby across two AZs (the lab uses AZ5 and AZ3).

**What each choice means:**
- **MySQL 5.7:** the database engine the lab's Discuz! installation expects.
- **Primary/standby:** two copies of the database. Writes go to the primary. Data is copied to the standby.
- **Two AZs:** if one data centre fails, the other one still has the data.

**Example:** ShopFast writes each new order to the primary in AZ5. If AZ5 fails, the standby in AZ3 takes over, and checkout keeps working after a short pause.

**Why use RDS instead of installing MySQL on the web server:** RDS takes care of backups, patching and failover. You do not have to manage those yourself.

---

### Section 2, Step 4: Install Discuz! and connect it to RDS

**What you do:** Open the Discuz! installer in a browser (`http://<public IP of ecs-web>/`). On the database page, enter:
- **Database host:** the RDS **private IP** (for example `192.168.2.100`)
- **Port:** 3306
- **Database name, username, password:** the values from the lab or the ones you set

**What is happening:** The installer connects from ecs-web to RDS over the private network, creates the forum tables, and saves the connection details in a config file on ecs-web.

**Why use the private IP and not the public one:** The private route stays inside your VPC, so the database is never exposed. It is also faster.

**Example:** The forum's posts and user accounts are written to RDS, not to the web server's disk. You could delete ecs-web and build a new one, and the forum data would still be there.

**Check:** If the installer says "cannot connect", check three things in order: the host is the private IP, the security group `sg-db` has port 3306 open with the right source, and the password is correct.

---

### Section 3, Step 1: View CPU and basic metrics for an ECS

**What you do:** In Cloud Eye, open the ECS monitoring page and look at CPU usage, memory, disk and network for ecs-web.

**What "basic monitoring" means:** Cloud Eye collects these values automatically, without you installing anything on the server. For ECS, the lab shows the default metrics.

**Example:** If CPU climbs to 90% every day at 20:00, the forum is busy every evening. You might add more servers or a scaling rule for that time.

**Why look at graphs:** Graphs show trends. A single number tells you almost nothing.

---

### Section 3, Step 2: Event alarm when the server restarts

**What you do:**
1. Create an **SMN topic** (for example `om-alert-topic`).
2. Add an **email subscription** with your address. **Open the confirmation email and click the link.** Until you confirm, no alert will be sent.
3. In Cloud Eye, create an **event alarm** for the restart event of ecs-web, and send the alarm to the SMN topic.

**What each part does:**
- **Event:** a one-time change, such as a reboot. Metrics show trends, but events show "this just happened".
- **Alarm:** a rule that says "when this event happens, do something".
- **SMN topic:** a channel. Anything sent to it is delivered to all its subscribers.
- **Subscription:** the email address that receives messages from the topic.

**Example:** The server restarts at 02:00. Cloud Eye records the restart event. The alarm sends a message to `om-alert-topic`. SMN emails the on-call engineer, who logs in to check the server.

**Watch out:** The lab says to select "the server with the Agent installed". This refers to the **Cloud Eye agent**, which collects extra OS-level data. It is a different program from **ICAgent**, which you install in Section 4 to send logs to LTS. Students often mix them up. Remember: Cloud Eye agent = metrics, ICAgent = logs.

---

### Section 4, Step 1: Create an LTS log group and log stream

**What you do:** In LTS, create a **log group** and inside it a **log stream**. Set the retention period (1 to 30 days; the default is 7).

**What each part does:**
- **Log group:** a folder for related logs (for example `lab-om-logs`).
- **Log stream:** one source inside the folder (for example `ecs-web-messages`).
- **Retention:** how many days LTS keeps the logs before deleting them.

**Example:** ShopFast might have a group called `checkout` with streams for `payment-service` and `web-frontend`. Each stream can be searched on its own.

---

### Section 4, Step 2: Install ICAgent on the ECS with AK/SK

**What you do:** Copy the ICAgent install command from the LTS console. Replace the placeholders with your AK and SK. Run the command on ecs-web.

**What the command does:** It downloads the ICAgent program, installs it, and registers it with your account. The AK/SK tells LTS which account the logs belong to.

**Security rule:** Replace the AK/SK **only on the ECS**, inside the command you run there. Do not type them into a chat or save them in a shared file.

**Example:** This is like giving a new delivery driver a key card. The card must be kept private. If it is shared, anyone can use it.

**Check:** After installation, the ICAgent status in the console should show as normal. If it shows as abnormal, the most common causes are a wrong AK/SK or a missing agency (permission) for LTS. Check those first.

---

### Section 4, Step 3: Collect /var/log/messages and parse it

**What you do:**
1. Add `/var/log/messages` as a collection path in the log stream.
2. Turn on **structuring parse** with a **colon (`:`) delimiter**.
3. View the logs as a table or a chart.

**What each part does:**
- `/var/log/messages` is a system log file on Linux. It records events from many system services.
- **Structuring parse** breaks each raw line into fields (columns) so you can search one field at a time.
- The **colon delimiter** tells the parser to split each line at every `:`.

**Example of a raw line and its fields:**

Sample line from the lab:
`May 9 10:14:14 ecs-web1 systemd:Stopped System Logging Service.`

**Why the colon needs care:** The time `10:14:14` also contains colons. When you split at every colon, the time is cut into pieces too: `May 9 10`, `14`, and `14 ecs-web1 systemd`. The clean split is the last one, `systemd` and `Stopped System Logging Service.` Use the preview in the console to see how the split looks before you save the rule.

**Why parse:** A table lets you filter "show only lines from ecs-web" or "show only lines that mention Stopped". Raw text is hard to search.

**Create a "Stopped" line to collect (lab command):** Over SSH on ecs-web, run:

`systemctl restart rsyslog`

- `systemctl`: the tool that controls background services on modern Linux.
- `restart`: stop the service, then start it again.
- `rsyslog`: the service that writes system logs into `/var/log/messages`.

**What happens:** The logging service stops, then starts. While it stops, it writes a line such as "Stopped System Logging Service" into `/var/log/messages`. That line is what the LTS parser captures.

**Example:** A shop closes its doors for a minute and reopens. The "closed" sign goes into the logbook, and the monitoring system reads the logbook.

**Why:** It creates a real "Stopped" line on purpose, so you can see the parser and alarm work. Usually this command needs admin rights, so prefix it with `sudo` if you are not root.

---

### Section 4, Step 4: Keyword alarm for "Stopped"

**What you do:** Create an LTS **keyword alarm** that fires when the logs contain the word **Stopped**. Send the alert to the SMN topic from Section 3.

**What the alarm does:** LTS scans new log lines. When it finds the keyword, it sends a message through SMN, and SMN emails you.

**Example:** ShopFast's payment service writes "Stopped" when it shuts down. The alarm emails the team within a few minutes, even if nobody is watching the screen.

**Timing:** The lab notes that the alert can take 1 to 3 minutes. Wait. Repeating the test does not make it faster and can clutter the logs.

**Simulate the web server failure (lab command):** Over SSH on ecs-web, run:

`systemctl stop httpd`

- `stop`: shut the service down now.
- `httpd`: the Apache web server that serves the Discuz! website.

**What happens:** The website goes offline, and Apache writes a stop message to the logs. LTS sees "Stopped" and the keyword alarm fires.

**Example:** This is a simulated outage, the same kind of failure a real site has if its web server crashes.

**Typo warning:** The lab text says `systemctl Stoppped httpd`. The correct command is `systemctl stop httpd`.

**Restore the site after the test (not in the lab text):** `systemctl start httpd` turns the web server back on. Run it so the forum is available again.

**Check (not in the lab text):** `systemctl status httpd` shows whether the service is running and its last few log lines.

---

## 5. The commands in this lab, explained

The lab asks you to type two Linux commands. They are explained in full inside Section 4 (Step 3 for `restart rsyslog`, Step 4 for `stop httpd`). This section is a quick reference you can use during the lab.

### Command 1: `systemctl restart rsyslog`

**Where:** On ecs-web, over SSH, as an administrator.

**What it does, word by word:**
- `systemctl`: the tool that controls services on modern Linux.
- `restart`: stop the service, then start it again.
- `rsyslog`: the service that writes system logs into `/var/log/messages`.

**What happens:** The logging service stops, then starts. While it stops, it writes a line such as "Stopped System Logging Service". That line is what the LTS parser captures.

**Example:** Think of a shop closing its doors for a minute and reopening. The "closed" sign goes into the log book, and the monitoring system reads the book.

**Why the lab does this:** It creates a real "Stopped" line on purpose, so you can see the whole chain work.

### Command 2: `systemctl stop httpd`

**Where:** On ecs-web, over SSH.

**What it does:**
- `stop`: shut the service down now.
- `httpd`: the Apache web server that serves the Discuz! website.

**What happens:** The website goes offline. The Apache service writes a stop message to the logs. LTS sees "Stopped" and the keyword alarm fires.

**Example:** This is a simulated outage. It is the same kind of failure a real site would have if its web server crashed.

**Lab text correction:** The lab text contains a typo, `systemctl Stoppped httpd`. The correct command is **`systemctl stop httpd`**. Use the correct version.

**Important:** After the test, bring the site back with:
`systemctl start httpd`
This command is not in the lab text. It is a good habit to restore the service after a test.

### Optional check (not in the lab text)

`systemctl status httpd` shows whether the service is running, and the last few log lines. Use it to confirm that `stop` worked before you wait for the alert.

---

## 6. The full chain (draw this)

```
Failure (restart rsyslog, or stop httpd)
  → log line contains "Stopped" in /var/log/messages
  → ICAgent sends the line to LTS
  → LTS keyword alarm fires
  → SMN topic
  → email to the engineer
```

**Task:** Draw this on paper. Next to each arrow, write which step of the lab does that job (for example: "ICAgent sends the line to LTS" → Section 4, Step 2).

---

## 7. Common mistakes

| Problem | Likely cause | Fix |
|---|---|---|
| Discuz! cannot connect to the database | Wrong host (public IP used), or sg-db has the wrong source | Use the RDS private IP; check the port 3306 rule |
| No alert email | SMN subscription not confirmed | Open the confirmation email and click the link |
| ICAgent shows abnormal | Wrong AK/SK, or LTS agency missing | Re-check the AK/SK; check the agency permission |
| Keyword alarm never fires | Parser or log path wrong, or you waited too little | Check the log stream shows new lines; wait 1 to 3 minutes |
| `systemctl Stoppped httpd` gives an error | Typo | Use `systemctl stop httpd` |
| Site stays down after the test | Service was stopped and not restarted | Run `systemctl start httpd` |

---

## 8. Review questions and answers

1. **Why is the database in a separate subnet?** So the web server and database do not share a network, which limits what an attacker can reach if the web server is compromised.
2. **Why is the source in sg-db set to ecs-web's IP and not 0.0.0.0/0?** Only the web server should talk to the database. A 0.0.0.0/0 source would allow anyone on the internet to try to connect to the database.
3. **What does primary/standby protect against?** The failure of one AZ. The standby in the other AZ takes over.
4. **Why use the private IP for the database host in Discuz!?** The traffic stays inside the VPC, the database is not exposed, and the connection is faster.
5. **What is the difference between a metric and an event?** A metric is a value tracked over time (such as CPU). An event is a one-time change (such as a restart).
6. **What is the difference between the Cloud Eye agent and ICAgent?** The Cloud Eye agent collects OS metrics for Cloud Eye. ICAgent sends logs to LTS.
7. **What does the colon delimiter do?** It splits each log line into fields at every colon, so fields can be searched and displayed as columns.
8. **Why does the lab run `systemctl stop httpd` on purpose?** To create a real failure and check that monitoring, logging and alerting catch it.
9. **What is the risk of pasting the AK/SK into a chat?** Anyone who sees it can act with your account's permissions. Rotate the key if this happens.

---

## 9. Points to know before you start

**1. The command typo.** The lab text says `systemctl Stoppped httpd`, with an extra "p". Linux does not recognise that name, so the web server never stops and the alarm never fires. Always type `systemctl stop httpd`.

**2. Two different agents.** The Cloud Eye agent sends server metrics to Cloud Eye (Section 3). ICAgent sends log lines to LTS (Section 4). Installing one does not install the other. If you install the wrong one, the alarm you are building will not get the data it needs.

**3. SSH is open to everyone in this lab.** The web server's security group allows port 22 from `0.0.0.0/0`, which means anyone on the internet can try to log in. Automated scanners constantly test open SSH ports. This is acceptable for a short lab, but in a real system you would set the source to your own address, such as `203.0.113.10/32`, so only you can connect.

**4. Keep your AK/SK and passwords private.** Anyone holding your AK/SK can act with that user's permissions. Do not paste them into chat, screenshots, shared documents or code. If you think a key has been exposed, disable or replace it in the console straight away.

**5. Confirm the email subscription.** After you add an email address to the SMN topic, SMN sends a confirmation email. Until you open it and click the link, the subscription is inactive, and no alarm email will arrive. Check your spam folder if you cannot find it.

**6. Wait for the alert.** The lab says the alert can take 1 to 3 minutes. Cloud Eye and LTS check data in intervals, so the alarm needs time to see the new line. Do not repeat the failure while you wait, because each repeat adds more log lines and makes the result harder to read.

---