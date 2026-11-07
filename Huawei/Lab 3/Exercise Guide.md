# Lab Handout: Highly Reliable Database Solution

**Level:** Intermediate
**Estimated time:** 2 hours
**Prerequisites:** Basic Huawei Cloud IaaS (VPC, ECS, security groups) and the database lectures

---

## What You Will Build

You will make a small forum website, **Discuz!**, reliable and fast.

- **Database reliability:** a managed MySQL database (RDS) with a standby copy, kept in sync by DRS.
- **Read scaling:** a read replica for heavy read traffic.
- **Speed:** a Redis cache (DCS) so the website does not query the database for every page.

```
Internet ── EIP ──► ecs-web (Discuz! web server, subnet-web)
                         │  MySQL port 3306, allowed by sg-db
                         ▼
                    rds-primary (MySQL 5.7, AZ1)  ──DRS sync──►  rds-standby (second AZ)
                         │
                         ├──► replica-discuz (read replica)
                         │
                    dcs-discuz (Redis cache) ◄── Discuz! checks the cache first
```

**Already set up for you (preset):** `vpc-primary`, `subnet-web`, `sg-web`, and `ecs-web`, which has an EIP. You will build the rest.

---

## Before You Start

1. **Log in with the lab account** provided in the exercise tutorial. Do not use your own account, because the lab resources are created under the lab account.
2. **Preset the lab environment** by clicking **Preset Lab**. This creates the account, the resources, and the network that the lab needs.
3. **Follow the region.** All resources must be in **AP-Singapore**, the same region as `vpc-primary`. Resources in another region cannot connect to the VPC.
4. **Keep the lab's names exact.** Later steps refer to resources by name (`subnet-db`, `sg-db`, `rds-primary`). Typing different names breaks the links between steps.
5. **Keep your passwords safe.** The admin password for Discuz! cannot be recovered if you lose it.

---

## Part 1: Basic Environment

**Goal:** Put the database on its own network, and open access only to the web server.

### Step 1.1: Create subnet `subnet-db`

1. Open **Service List > Virtual Private Cloud**.
2. Go to **Subnets** and click **Create Subnet**.
3. Set:
   - **VPC:** `vpc-primary`
   - **Name:** `subnet-db`
   - **IPv4 CIDR Block:** `192.168.2.0/24`
   - Keep the other values as default.
4. Click **OK**. You should now see `subnet-web` and `subnet-db` in the list.

**Why:** The database gets its own subnet, separate from the web server's subnet. Later, you can apply rules to the database tier without touching the web tier.

**Remember from the network lecture:** a `/24` subnet has 256 addresses, and 5 are reserved, so 251 are usable.

### Step 1.2: Create security group `sg-db`

1. Go to **Access Control > Security Groups** and click **Create Security Group**.
2. Set:
   - **Name:** `sg-db`
   - **Template:** Fast-add rule
   - **Inbound Rules:** select **MySQL (3306)**
3. Click **OK**.

**Why:** A security group is a firewall for instances. The database needs port 3306 open for MySQL connections, and nothing else.

### Step 1.3: Limit the database rule to the web tier

1. Open `sg-db`, go to **Inbound Rules**, and find the row for **TCP 3306**.
2. Click **Modify** and change **Source** from an IP address to **Security group**.
3. Select `sg-web` as the source and confirm.

**Why this matters:**
- Starting with `0.0.0.0/0` would let any address reach the database. The lab changes the source so only web servers can connect.
- Using a security group instead of a single IP means that when you add web servers to `sg-web`, they can reach the database without editing the rule.

> **Think about it:** Why would a single IP address rule be harder to maintain than a security group rule when you scale to ten web servers?

### Step 1.4: Buy the primary RDS instance `rds-primary`

1. Open **Service List > Relational Database Service** and click **Buy DB Instance**.
2. Set:

| Setting | Value | Why |
|---|---|---|
| Billing Mode | Pay-per-use | Pay only for the time you use it |
| Region | AP-Singapore | Same region as the VPC |
| DB Instance Name | `rds-primary` | The name used later in the lab |
| DB Engine / Version | MySQL 5.7 | The version Discuz! supports in this lab |
| DB Instance Type | Primary/Standby | Two copies for automatic failover |
| Primary AZ | AZ1 | One data center |
| Standby AZ | AZ5 | A different data center, so one failure does not take out both |
| Instance Class | Dedicated 2 vCPUs \| 4 GB | Enough for the lab |
| Storage | Cloud SSD, 40 GB | Fast disk for database files |
| VPC / Subnet | `vpc-primary` / `subnet-db` | Puts the database on the private database subnet |
| Port | 3306 | The MySQL default |
| Security Group | `sg-db` | The firewall from Step 1.2 |
| Password | Your own, kept safe | The root password for the database |

3. Click **Next**, confirm the details, select the agreement, and click **Submit**.

**Why Primary AZ and Standby AZ are different:** if one data center loses power, the other still has a copy of the database.

### Step 1.5: Install Discuz! and connect it to the database

1. Open **Service List > Elastic Cloud Server** and copy the **EIP** of `ecs-web`.
2. In a browser on the lab desktop, open `http://EIP:80`.
3. Click **I agree**. The installer checks that the required folders are writable and that the needed PHP functions exist.
4. Choose **A new installation Discuz! X (Contain UCenter Server)** and click **Next**.
5. Enter these values:
   - **Database server:** the IP address of `rds-primary` (from the RDS console)
   - **Database Pw:** the root password you set in Step 1.4
   - **Admin PW:** a password for the Discuz! admin account (keep it safe)
   - **Repeat PW:** the same admin password
6. Click **Next** and wait for the installation to finish.
7. Open `http://EIP:80` again, log in as admin, and confirm the site works.

**Why:** This connects the web application to the database. The website now stores its data in RDS, not on the web server's disk.

---

## Part 2: Highly Reliable Database Design

**Goal:** Protect the data with a standby copy, and add a read replica for growth.

### Step 2.1: Buy the standby instance `rds-standby`

1. Click **Buy DB Instance** again.
2. Use the same settings as `rds-primary`, with one change: **DB Instance Name** is `rds-standby`.
3. Submit, then wait until both instances are shown on the Instances page.
4. **Write down the floating IP address of `rds-standby`.** You need it in Step 2.2.

**Why:** This second instance is the destination for the DRS sync. Its settings match the primary so the copy behaves the same way.

> **Note for students:** Primary/Standby instances already keep an internal standby. This lab creates a separate instance on purpose, so you can practice a second, cross-instance copy with DRS. It is not the usual way to add high availability to one database.

### Step 2.2: Create the DRS task `DRS-discuz`

**What DRS is:** Data Replication Service (DRS) copies data between databases in real time. It is used for migration, synchronization, and disaster recovery.

1. Open **Service List > Data Replication Service** and click **Create Migration Task**.
2. In the first page, set:
   - **Region:** AP-Singapore
   - **Task Name:** `DRS-discuz`
   - **Data flow:** select the option the lab specifies
   - **Source DB Engine / Destination DB Engine:** MySQL / MySQL
   - **Network Type:** VPC
   - **Source DB Instance:** `rds-primary`
   - **Replication Instance Subnet:** `subnet-db`
   - **Migration Type:** **Full + Incremental**
3. Click **Next**.

**Choosing the migration type:**

| Mode | What it does | When to use it |
|---|---|---|
| **Full** | Copies all data once | Short service interruption is acceptable. Do not write to the source during the copy, or new data will be missed. |
| **Full + Incremental** | Copies all data, then keeps copying changes from the logs | You want little or no downtime. The source stays usable while the copy runs. |

The lab uses **Full + Incremental**, because the website keeps running during the migration.

4. Click **Create Now**, then click **Test Connection** on the task.
5. For the destination database, enter:
   - The **IP address** of `rds-standby` (from Step 2.1)
   - The **root password** you set on `rds-standby`
6. Click **Test Connection**, then **Next**, and agree to the dialog.
7. On the Configure Source and Destination Databases page, confirm the migrate-account remarks, then click **Next**.
8. Wait for the **precheck** to finish. Fix any failed items before continuing.
9. Click **Confirm Details**, then **OK**, then **Next**.
10. For **Start Time**, choose **Start upon task creation**. Click **Submit** and confirm the precautions.
11. Wait for the full copy to finish. Then check that **incremental sync** is running.

**Why each check matters:**
- **Test Connection** proves DRS can reach both databases before it starts.
- **Precheck** finds problems early, such as unsupported objects or missing permissions.
- **Incremental sync** keeps the standby close to the primary after the full copy finishes.

### Step 2.3: Create the read replica `replica-discuz`

**What a read replica does:** It receives changes from the primary and answers read queries. Reads can move to the replica, which lowers the load on the primary.

1. Open **Relational Database Service**. On the Instances page, find `rds-primary`.
2. Choose **More > Create Read Replica**.
3. Set:
   - **Billing Mode:** Pay-per-use
   - **DB Instance Name:** `replica-discuz`
   - **DB Engine / Version:** MySQL 5.7
   - **Storage:** Cloud SSD, 40 GB
   - **AZ:** AZ1
   - **Instance Class:** Dedicated 2 vCPUs | 4 GB
   - **VPC / Subnet:** `vpc-primary` / `subnet-db`
   - **Security Group:** `sg-db`
4. Click **Next**, select the agreement, and click **Submit**.
5. Back in the RDS console, click the plus sign (+) next to `rds-primary` to see the replica under it.

**Standby vs read replica (important for the exam):**

| | Standby | Read replica |
|---|---|---|
| Purpose | Failover and restoration | Extra read capacity |
| Serves application reads? | No | Yes |
| Example here | `rds-standby` (DRS target) | `replica-discuz` |

---

## Part 3: Cache Database

**Goal:** Serve repeated page data from memory, so the database and web server do less work.

### Step 3.1: Buy the cache instance `dcs-discuz`

**What DCS is:** Distributed Cache Service (DCS) is an in-memory cache compatible with Redis. It stores data in RAM, so reads are very fast.

1. Open **Service List > Distributed Cache Service (for Redis)** and click **Buy DCS Instance**.
2. Set:
   - **Billing Mode:** Pay-per-use
   - **Region:** AP-Singapore
   - **Cache Engine:** Redis
   - **CPU Architecture:** x86
   - **Version:** 5.0
   - **Instance Type:** Master/Standby
   - **Primary AZ:** AZ1
   - **Standby AZ:** AZ2 (the lab lists "Primary AZ" twice; the second one is the standby)
   - **Instance Specification:** `redis.ha.xu1.tiny.r2.512`
   - **VPC / Subnet:** `vpc-primary` / `subnet-db`
   - **Name:** `dcs-discuz`
   - **Password Protected:** No (acceptable for this lab only)
   - **Parameter Configuration:** Default templates
3. Click **Next**, confirm, and click **Submit**.
4. On the **Cache Manager** page, click `dcs-discuz` and **record its IP address**.

**Why a Master/Standby cache:** if the master fails, the standby takes over, so the cache stays available.

**Why "Password Protected: No":** the lab is isolated, so it is acceptable here. In production, enable password protection.

### Step 3.2: Connect Discuz! to the cache

1. In the ECS console, find `ecs-web`, choose **More > Reset Password**, and set a new password. Keep it safe.
2. Restart `ecs-web` and copy its EIP.
3. Open an **Xfce terminal** on the lab desktop and connect:

```bash
ssh root@EIP
```

Replace `EIP` with the EIP of `ecs-web`, and enter the password you set.

4. Install the PHP extension that lets PHP talk to Redis:

```bash
yum install php-redis -y
```

**Why:** Discuz! is written in PHP. Without this extension, PHP cannot connect to Redis.

5. Restart the web server so the extension loads:

```bash
systemctl restart httpd
```

6. Open the Discuz! configuration file:

```bash
vi /var/www/html/config/config_global.php
```

7. Find the section **CONFIG MEMORY** and set the **redis server** value to the **IP address of `dcs-discuz`**. Save and exit.

**Why:** This tells Discuz! where the cache is. After this change, Discuz! checks Redis before asking the database.

8. Open `http://EIP:80` in a browser and load the site.

**Cache-aside pattern (what is happening):**

```
1. Discuz! asks Redis for the page data.
2. Cache hit   → Redis returns it. The database is not used.
3. Cache miss  → Discuz! reads the database, then stores the result in Redis.
```

---

## Part 4: Check Your Work

Before you finish, confirm:

- [ ] Discuz! opens through the EIP and you can log in as admin
- [ ] `rds-primary` and `rds-standby` are on different AZs
- [ ] The DRS task `DRS-discuz` shows incremental sync running
- [ ] `replica-discuz` appears under `rds-primary`
- [ ] `dcs-discuz` is running, and `config_global.php` points to its IP
- [ ] The site loads after the cache change

---

## Part 5: Clean Up

Pay-per-use resources cost money while they run. When you finish:

1. Delete the DRS task `DRS-discuz`.
2. Delete `replica-discuz`, `rds-standby`, `rds-primary`, and `dcs-discuz`.
3. Check the lab's usage or billing page to confirm nothing is still running.

> The lab says resources may be reclaimed when the exercise ends. Still check, and delete anything you created yourself.

---

## Key Concepts Summary

| Concept | One-line explanation |
|---|---|
| Subnet | A section of the VPC's address range (here, `192.168.2.0/24`) |
| Security group | A firewall for instances; here it lets only web servers reach the database |
| Primary/Standby (AZ1 and AZ5) | Two database copies in different data centers for automatic failover |
| DRS Full + Incremental | Copies all data, then keeps copying changes, with little downtime |
| Read replica | An extra read-only copy that takes read traffic off the primary |
| DCS (Redis) | An in-memory cache that serves repeated data quickly |
| Cache-aside | Check the cache first; on a miss, read the database and store the result |

---

## Review Questions

1. Why does the lab change the `sg-db` rule source from `0.0.0.0/0` to `sg-web`?
2. What is the difference between a standby instance and a read replica?
3. When would you choose Full migration instead of Full + Incremental?
4. What happens to a request for a page that is already in Redis?
5. Why must you test the DRS connections before you start the task?

---

*Based on the Huawei Cloud Highly Reliable Database Solution lab. Console labels and product limits can change, so compare each step with the lab page on the day.*