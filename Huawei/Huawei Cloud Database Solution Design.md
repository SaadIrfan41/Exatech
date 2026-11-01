# Huawei Cloud Database Solution Design

**Level:** Beginner
**Prerequisites:** Compute, Storage, and Network lectures
**What you will do:** Learn how to store data safely in Huawei Cloud, choose the right database for each job, keep it available, and move existing databases to the cloud.

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. Explain who manages what in on-premises, IaaS, and managed (PaaS) database deployments.
2. Choose between relational, NoSQL, and caching services for a workload.
3. Explain how a primary/standby pair keeps a database available.
4. Explain the difference between backup, replication, and disaster recovery.
5. Describe how a cache reduces database load.
6. Explain how DRS migrates a database with minimal downtime.

---

## Running Example: The ShopFast Database Layer

ShopFast's data has three jobs:

| Data | Example | Best fit |
|---|---|---|
| Orders and customer accounts | Must never be lost or half-written | Relational database (RDS) |
| Product pages and shopping carts | Read thousands of times per second | Cache (DCS) in front of the database |
| Old on-premises MySQL | Must move to the cloud | DRS migration |

---

## Part 1: Who Manages What?

Where a database runs decides how much work you do yourself.

| Layer | On-premises | Cloud server (IaaS) | Managed database (PaaS, for example RDS) |
|---|---|---|---|
| Data center, power, hardware | You | Huawei Cloud | Huawei Cloud |
| Operating system | You | You | Huawei Cloud |
| Database engine installation and patching | You | You | Huawei Cloud |
| Backups, high availability, failover | You | You | Huawei Cloud (you choose the options) |
| Database design, queries, indexes | You | You | You |

**Key idea:** With a managed database, you still design the data and write efficient queries. Huawei Cloud handles the servers, the engine, patches, and most of the backup and failover work.

---

## Part 2: Choosing a Database Type

| Type | Stores data as | Use it for | Huawei Cloud service |
|---|---|---|---|
| **Relational** | Tables with rows and columns, linked by keys | Orders, payments, accounts | RDS for MySQL, RDS for PostgreSQL, GaussDB |
| **Document** | Flexible JSON-like documents | Product catalogs with varied fields | DDS (MongoDB-compatible) |
| **Key-value / cache** | Simple key and value pairs in memory | Session data, hot product pages | DCS, GeminiDB Redis API |
| **Analytics** | Large volumes, queried for reports | Sales dashboards | GaussDB(DWS) |

**Relational** means data is organized in tables, and the database checks that related rows stay consistent. For example, an order cannot point to a customer who does not exist.

**NoSQL** means a database that does not use fixed tables. It is often used when the data shape changes or when you need very high speed for simple lookups.

**Quick check:** Which type fits a shopping cart that must survive a server restart? Which fits a monthly sales report?

---

## Part 3: High Availability with Primary and Standby

A database can fail. A **primary/standby** pair protects against this.

```
   App servers (AZ 1 and AZ 2)
            │
            ▼
   ┌────────────────────┐   real-time sync   ┌────────────────────┐
   │ Primary (AZ 1)     │ ─────────────────► │ Standby (AZ 2)     │
   │ serves all traffic │                    │ used only for      │
   └────────────────────┘                    │ failover/restore   │
                                              └────────────────────┘
```

### 3.1 How it works

- The primary handles all reads and writes.
- The standby receives every change in near real time.
- If the primary fails, the system promotes the standby. This is called **failover**.
- A failover normally completes within seconds. Some extreme conditions can take longer.

### 3.2 What students must know

- **The standby cannot serve your application.** You access only the primary during normal operation. The standby exists for failover and restoration.
- **Connections are interrupted during failover.** Applications must reconnect automatically. Build reconnect logic into your code.
- **Place primary and standby in different AZs.** Otherwise one data-center failure can take down both.
- **You can switch manually** between primary and standby, for example for maintenance or rack-level disaster recovery. Schedule manual switchovers in off-peak hours to avoid congestion.
- **A single-node instance has no failover.** It is cheaper, but not suitable for important workloads.
- **Failover priority** can be set to Reliability (protects data consistency first, the default) or Availability (keeps the database online first). Choose based on what matters most.

**Quick check:** ShopFast's order database fails over from AZ 1 to AZ 2. Customers see a brief error. What should the application do?

---

## Part 4: Backup, Replication, and Disaster Recovery

These three ideas are often confused, but each protects against a different problem.

| Idea | What it protects against | Example |
|---|---|---|
| **Replication** (primary/standby) | Hardware or data-center failure | An AZ loses power, the standby takes over |
| **Backup** (point-in-time recovery) | Mistakes and data corruption | A developer runs `DELETE` without a `WHERE` clause; ShopFast restores the database to 10:59 a.m. |
| **Disaster recovery (DR)** | A whole region goes down | An entire region fails; a standby database in another region takes over |

**The critical lesson:** Replication copies everything, including mistakes. If a bad query deletes rows on the primary, the standby deletes them too. Only a backup lets you go back to an earlier time.

RDS supports restoring data to a chosen point in time, so ShopFast can recover from a bad change.

**Quick check:** A developer accidentally deletes last Tuesday's orders. Which protects you, replication or backup?

---

## Part 5: Speeding Up Reads with a Cache

Reading from a database is slower than reading from memory. A **cache** stores frequently used results in memory.

The most common pattern is **cache-aside**:

```
1. The app asks the cache for product 42.
2. Cache hit  → the cache returns the data. Done.
3. Cache miss → the app reads the product from the database.
4. The app stores the result in the cache for next time.
```

**ShopFast example:** The product page for a popular item is read thousands of times an hour. After the first read, the cache serves almost all of them, so the database handles far fewer requests.

**Caution:** Cached data can be out of date for a short time. Set an expiry time (TTL) that matches how often the data changes. Prices may need a short TTL. Store images and static pages in OBS or a CDN instead of the cache.

**Huawei Cloud options:** DCS is an in-memory cache compatible with Redis. GeminiDB Redis API is a distributed NoSQL service with a Redis interface.

**Quick check:** A product price changes at noon. The cache holds the old price for an hour. What setting controls this, and what should it be?

---

## Part 6: Moving a Database to the Cloud with DRS

**Data Replication Service (DRS)** copies data from a source database to a destination, in real time. DRS keeps the two in sync while you move your application, so downtime is minimal.

### 6.1 How a DRS migration works

1. **Prepare the source.** Create a database account for DRS with replication permissions. Make sure the network can reach the source.
2. **Prepare the destination.** Create the target database, such as RDS for MySQL.
3. **Create a replication instance.** DRS runs a service instance that connects to both databases.
4. **Test the connections** to the source and the destination.
5. **Run a full copy, then incremental sync.** DRS copies existing data, then keeps replaying the changes.
6. **Compare the data.** DRS checks that the source and destination match.
7. **Cut over.** Switch the application to the new database, then stop the DRS task.

### 6.2 Network for a public migration

For an on-premises source over the public network:
- Create an EIP for the DRS instance.
- Add that EIP to the firewall allowlist of the on-premises database.

### 6.3 What "minimal downtime" means

DRS is designed to keep downtime small. Students should not expect zero downtime. The cutover step, where traffic moves to the new database, always involves a short pause. Check the current DRS documentation for the expected impact on your workload.

**Quick check:** Why must DRS compare data before cutover?

---

## Part 7: ShopFast Database Architecture

```
                      Internet
                          │
                    Elastic Load Balancer
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
   Web App 1 (AZ 1)                Web App 2 (AZ 2)
          │                               │
          ├──── DCS cache (product pages, sessions) ────┤
          │                               │
          └───────────────┬───────────────┘
                          ▼
              RDS primary (AZ 1) ◄─── sync ───► RDS standby (AZ 2)
                          │
                 Point-in-time backups
                          │
              Region B: DR copy of the database
```

**How to read this:**
1. Requests reach the web apps through the load balancer.
2. Most product reads come from the cache.
3. Cache misses and all writes go to the RDS primary.
4. The standby in another AZ takes over if the primary fails.
5. Backups let ShopFast recover from mistakes, and a DR copy protects against a regional failure.

---

## Part 8: Cost and Operations

| Practice | Why it helps |
|---|---|
| Right-size the database instance to the workload | Avoid paying for capacity you do not use |
| Remove unused read replicas | Each replica costs money |
| Use a cache for read-heavy data | Reduces the load, and sometimes the size, of the database |
| Choose billing modes that match the workload | Pay-per-use for unpredictable load; longer plans for steady load |
| Set backup retention deliberately | Keeps recovery options without storing data forever |
| Test failover and restore regularly | A backup you have never restored is not proven |

---

## Part 9: Quiz

Try these before the lecture ends. Answers will be discussed in class.

**Q1 (Single choice):** Which service should store ShopFast's orders, which must stay consistent?
- A. RDS (relational database)
- B. DCS (cache)
- C. OBS (object storage)

**Q2 (Single choice):** During normal operation, can ShopFast's application read from the standby instance?
- A. Yes, to share the read load
- B. No, the standby is used for failover and restoration

**Q3 (Multiple choice):** Which statements are correct?
- A. Replication copies a bad delete to the standby.
- B. Point-in-time backup can restore data from before a mistake.
- C. Replication protects against accidental deletes.
- D. Primary and standby should be in different AZs.

**Q4 (Single choice):** A cache miss happens. What should the application do?
- A. Return an error to the customer
- B. Read from the database, then store the result in the cache
- C. Write the data to the cache only

**Q5 (Scenario):** ShopFast's data center is closing, and the database must move to Huawei Cloud with minimal downtime. Which service should you use?

**Q6 (Scenario):** A developer deleted yesterday's customer records by mistake. Which option restores them?

**Q7 (Scenario):** A new team is choosing a Redis-compatible service. Which version should they choose for new projects, 5.0 or 6.2?

---

## Glossary

| Term | Meaning |
|---|---|
| **Cache-aside** | A pattern where the application checks the cache first, then the database on a miss |
| **Cache hit / miss** | A hit finds the data in the cache; a miss does not |
| **Cutover** | The moment traffic switches to the new database during a migration |
| **DCS** | Distributed Cache Service: an in-memory cache compatible with Redis |
| **DDS** | Document Database Service: a MongoDB-compatible database |
| **DR** | Disaster recovery: a plan to keep services running after a major failure |
| **DRS** | Data Replication Service: real-time migration and synchronization |
| **Failover** | Switching from a failed primary to the standby |
| **Point-in-time recovery** | Restoring a database to a chosen moment from backups |
| **Primary/standby** | A pair where one instance serves traffic and the other stands by for failover |
| **RDS** | Relational Database Service: managed relational databases |
| **Relational database** | A database that stores data in linked tables |
| **Replication** | Copying changes from one database to another in near real time |
| **TTL** | Time to live: how long cached data is kept before it expires |

---

## Summary

- **Managed databases** handle servers, engines, patches, and much of the backup and failover work. You still design the data and queries.
- **Choose by data type:** relational for orders, document for flexible catalogs, cache for fast repeated reads.
- **Primary/standby** keeps a database available. Failover takes seconds, and applications must reconnect.
- **Replication is not backup.** Backups protect against mistakes, replication against hardware failure, and DR against regional failure.
- **Caches** reduce database load. Set expiry times to limit stale data.
- **DRS** migrates databases with minimal downtime, and you should always compare the data before cutover.

---

*This handout is based on Huawei Cloud's database documentation. Figures, versions, and features change, so confirm current details in the official documentation before class.*