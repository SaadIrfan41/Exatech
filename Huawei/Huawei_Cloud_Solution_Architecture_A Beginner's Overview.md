# Huawei Cloud Solution Architecture: A Beginner's Overview

---

## 1. Introduction

A **solution architect** designs the overall structure of a cloud system before anyone builds it. The architect decides which cloud services to use, how they connect, how they stay online when something fails, how secure they are, what they cost, and how they are managed day to day.

This overview introduces the basic ideas you need before studying detailed services. You do not need to memorize every term on the first read. Use the glossary in Section 2 as a reference.

By the end of this overview, you should be able to:

- Explain what Regions, Availability Zones, and subnets are.
- Describe the five pillars of cloud architecture and give an example of each.
- Explain why systems are split into layers and services.
- Read a simple high-availability architecture diagram.

---

## 2. Key Terms

| Term | Meaning |
| :--- | :--- |
| **Region** | A geographic location where a cloud provider runs its data centers (for example, a China or Asia-Pacific region). |
| **Availability Zone (AZ)** | One or more data centers inside a Region with separate power and networking. If one AZ fails, others in the same Region keep running. |
| **VPC (Virtual Private Cloud)** | Your own private, isolated network inside the cloud. |
| **Subnet** | A smaller section of a VPC, such as a "front-end" subnet for public-facing servers or a "data" subnet for databases. |
| **Security Group** | A set of firewall rules that control which traffic is allowed to reach a server. |
| **ELB (Elastic Load Balancer)** | A service that spreads incoming traffic across several servers so that no single server is overloaded. |
| **NAT Gateway** | Lets servers in private subnets reach the internet (for example, to download updates) without being reachable from the internet. |
| **Auto Scaling (AS)** | Automatically adds or removes servers based on load, such as CPU use or number of requests. |
| **EIP (Elastic IP)** | A fixed public IP address that you can attach to a server. |
| **EVS (Elastic Volume Service)** | Cloud disk storage attached to servers. |
| **RDS (Relational Database Service)** | A managed database service, so the cloud provider handles backups, patching, and replication. |
| **GaussDB** | Huawei's own high-performance, distributed database engine. |
| **DCS (Distributed Cache Service)** | A managed cache service, usually Redis or Memcached, used to speed up repeated reads. |
| **DDM (Distributed Database Middleware)** | Splits one large database across several smaller databases (called sharding) to handle more writes. |
| **CDN (Content Delivery Network)** | Stores copies of static files (images, videos, scripts) on servers close to users so they load faster. |
| **WAF (Web Application Firewall)** | Inspects web traffic and blocks common attacks such as SQL injection. |
| **Anti-DDoS (AAD)** | Protects against Distributed Denial of Service attacks, which flood a service with traffic to take it offline. |
| **Message bus (Kafka / RabbitMQ)** | Software that passes messages between services so that one service does not have to wait for another. On Huawei Cloud these are offered as managed services. |
| **RPC (Remote Procedure Call)** | A way for one service to call a function in another service over the network, usually for fast, direct requests. |
| **MTBF (Mean Time Between Failures)** | The average time a system runs before it fails. |
| **MTTR (Mean Time To Recover)** | The average time it takes to restore a system after a failure. |
| **IOPS (Input/Output Operations Per Second)** | How many read or write operations a storage system can handle each second. |

---

## 3. Core Infrastructure Concepts

Before looking at architecture patterns, understand how the building blocks fit together.

**Regions and Availability Zones.** A Region is a geographic area, and each Region contains several AZs. AZs are placed far enough apart that a fire, power cut, or flood in one does not affect the others, but close enough to communicate with low delay. Putting an application in more than one AZ is the most common way to protect it from data-center failures.

**VPC and subnets.** A VPC is your private network in the cloud. You divide it into subnets, and each subnet has a purpose:

- A **front-end (public) subnet** holds servers that receive traffic from users.
- An **application subnet** holds the business logic. It should not be directly reachable from the internet.
- A **data subnet** holds databases and caches. It should be the most restricted subnet, reachable only from the application subnet.

Keeping each layer in its own subnet means that a problem in one layer is less likely to reach the others.

**Security groups.** Security groups act as firewalls. A good rule is to allow only the traffic each layer actually needs. For example, the database should accept connections only from the application servers, not from the whole internet.

**Load balancers.** An ELB sits in front of a group of servers and sends each request to a healthy server. If a server fails, the ELB stops sending traffic to it.

---

## 4. The 5 Pillars of Cloud Solution Architecture

A good architecture balances five goals. Improving one often costs something in another, so architects make tradeoffs rather than optimizing a single area.

### Pillar 1: Security

**Goal:** Protect data and systems from attacks and misuse, while still letting users access the system easily.

**Key ideas:**

- **Follow the rules that apply to you.** Security requirements depend on the law (for example, data protection laws such as GDPR). Choose controls that meet those requirements, not the most expensive tools available.
- **The weakest link decides the strength of the system.** One unpatched server or one overly open firewall rule can expose the whole system. This is sometimes called the "bucket effect," after the bucket whose shortest stave decides how much water it can hold.
- **Defense in depth.** Protect each layer: the network edge, the operating system, the application code, and stored data. If one layer fails, another still protects the system.
- **Plan for breaches.** Assume that an attack will eventually succeed, and prepare a process to detect it, contain it, and recover quickly.

**Example:** Encrypt stored customer data, so that a stolen disk is useless without the key.

### Pillar 2: Reliability and High Availability (HA)

**Goal:** Keep the service running, and recover quickly when something fails.

**Availability** is the share of time a system is working. It is calculated as:

> Availability = MTBF / (MTBF + MTTR)

In practice, availability targets are often described as allowed downtime:

| Availability | Downtime allowed per year |
| :--- | :--- |
| 99.9% | About 8 hours 45 minutes |
| 99.99% | About 52 minutes |
| 99.995% | About 26 minutes |

**Key ideas:**

- **Remove single points of failure (SPOF).** If only one server or one database can serve requests, that component will eventually take the whole system down. Run at least two of each critical component.
- **Use multiple AZs.** Active-active means both AZs serve traffic at the same time. Active-standby means one AZ serves traffic and the other waits, ready to take over.
- **Loosely coupled services.** If the order service depends directly on the email service, an email outage can block orders. A message bus lets orders be accepted and processed even when the email service is slow or down.

**Example:** A web application runs in two AZs behind a load balancer. If one AZ loses power, the load balancer sends all traffic to the other AZ, and users may see only a short delay.

### Pillar 3: Performance Optimization

**Goal:** Respond quickly to users, even when the load changes.

**Four things to measure:**

- **Compute latency:** how long one request takes to process.
- **Network throughput:** how much data can move per second.
- **Storage IOPS:** how many read and write operations storage can handle per second.
- **Database concurrency:** how many queries the database can serve at the same time without slowing down.

**Key ideas:**

- **Cache frequently read data.** Use a CDN for images and scripts, and a cache such as DCS (Redis) for database results that rarely change.
- **Scale automatically.** Auto Scaling adds servers when CPU or request count rises, and removes them when demand drops.
- **Plan for realistic peaks.** Size capacity a little above normal peak demand. Designing for theoretical maximums wastes money.

**Example:** A product page loaded 10,000 times per minute is served from a cache, so only a few requests reach the database.

### Pillar 4: Cost Optimization

**Goal:** Get the most value from the money spent on cloud resources.

**Key ideas:**

- **Pay only for what you use.** Pay-as-you-go pricing matches cost to actual use.
- **Avoid paying for idle capacity.** Use Auto Scaling and schedule smaller capacity during off-peak hours, instead of running large servers all day.
- **Audit resources regularly.** Look for unused public IPs (EIPs), disks not attached to any server (EVS), and databases that are much larger than their workload needs.

**Example:** An online shop that is busy only during the day can scale down at night, saving the cost of unused servers.

### Pillar 5: Maintainability and Operations

**Goal:** Make the system easy to monitor, change, and repair, with as little manual work as possible.

**Key ideas:**

- **Monitor everything.** Track health, performance, and errors. Huawei Cloud provides Cloud Eye for infrastructure monitoring and Application Operations Management (AOM) for application monitoring.
- **Automate with Infrastructure as Code (IaC).** Define servers and networks in configuration files, so they can be recreated the same way every time.
- **Replace, do not repair.** When a server behaves badly, terminate it and start a new one from a clean image, instead of fixing it by hand. Hand fixes are hard to repeat and easy to forget.
- **Use managed services.** Let the provider handle backups, operating-system patching, and database replication where possible, so your team can focus on the application.

**Example:** A new server is created from a standard image and configured automatically, so it matches every other server in the group.

---

## 5. Architecture Lifecycle

Architecture work happens in two main stages.

**Stage 1: Architecture Design**

- Break the system into services with clear responsibilities.
- Plan the network, including Regions, AZs, VPCs, and subnets.
- Plan high availability and redundancy.
- Define security rules and scaling policies.

**Stage 2: Architecture Acceptance**

- Check the built environment against the design.
- Run security and compliance reviews.
- Run load tests to find bottlenecks.
- Test failover, so you know the system recovers when a component is switched off.
- Get operations staff to confirm they are ready to run the system before it goes live.

---

## 6. Case Study: High-Traffic E-Commerce

This case study is based on an online store running large promotions, such as holiday sales or product launches. It shows how the five pillars combine in a real design. The traffic numbers are examples to illustrate scale, not targets for every project.

### The Challenges

- **Traffic spikes:** Many users arrive at the same moment, and orders and payments must still be processed.
- **Bots and scalpers:** Automated scripts try to buy up stock before real customers can. This is a security problem as well as a fairness problem.
- **DDoS attacks:** Attackers may flood the public website during a sale to take it offline.

### The Architecture

```
[ Users on the Internet ]
          |
          v
+-----------------------------------------+
| Edge: Anti-DDoS + WAF + CDN             |   Blocks attacks, serves static files
+-----------------------------------------+
          |
          v
+-----------------------------------------+
| Elastic Load Balancer (ELB)             |   Spreads requests across servers
+-----------------------------------------+
          |
          v
+-----------------------------------------+   +-----------------------------------------+
| Availability Zone 1                     |   | Availability Zone 2                     |
|                                         |   |                                         |
|  Front-end subnet: web servers (AS)     |   |  Front-end subnet: web servers (AS)     |
|  Application subnet: app servers (AS)   |   |  Application subnet: app servers (AS)   |
|  Data subnet: cache (DCS), database     |   |  Data subnet: standby database          |
|  NAT Gateway: outbound updates          |   |                                         |
+-----------------------------------------+   +-----------------------------------------+
                       database replication between AZ1 and AZ2
```

**How to read it:**

1. Requests reach the edge first, where attacks are filtered and static files are served from the CDN.
2. The ELB sends each remaining request to a web server in either AZ.
3. Web servers pass the request to application servers in the application subnet, which the internet cannot reach directly.
4. Application servers read from the cache when possible, and from the primary database when necessary.
5. The database in AZ1 is copied to a standby in AZ2. If AZ1 fails, the standby takes over.

Auto Scaling in each AZ adds web and application servers during a sale and removes them afterward.

### Mapping the Challenges to Solutions

| Challenge | Pillars | Solution |
| :--- | :--- | :--- |
| Traffic spikes during flash sales | Performance, Reliability | Auto Scaling for web and application servers. Run the flash-sale pages on their own service, separate from the main site, so a sale cannot slow the rest of the store. |
| Database write bottlenecks | Performance, Reliability | Split the database by function (for example, orders and users in separate databases). Use DDM to shard large tables. Use write-through caching with DCS to reduce load. |
| Bots and scalpers | Security | Use WAF and API gateway rules to detect suspicious patterns. Add rate limits (for example, a maximum number of requests per user per minute), and use checks such as CAPTCHA at checkout. |
| DDoS attacks | Security | Route all public traffic through Anti-DDoS before it reaches the load balancer. |
| Power or AZ outage | Reliability, HA | Run application servers in both AZs, and keep a standby database in the second AZ. |

### Tradeoffs in This Design

Every choice above has a cost. Running servers in two AZs and keeping a standby database makes the system more reliable, but it roughly doubles the cost of those components. An architect decides how much reliability the business needs and accepts the cost that comes with it. A small internal tool may not need a standby database; an online payment system almost certainly does.

---

## 7. Review Questions

1. What is the difference between a Region and an Availability Zone?
2. Why should a database sit in its own subnet, not the front-end subnet?
3. If a system has 99.9% availability, roughly how much downtime is allowed per year?
4. Why does one unpatched server affect the security of the whole system?
5. Give one example of a single point of failure, and explain how you would remove it.
6. Why might an architect use a message bus between the order service and the email service?
7. Name one cost-saving measure and one tradeoff it might introduce.

---

## 8. Summary

- A solution architect designs the structure of a cloud system, balancing security, reliability, performance, cost, and operations.
- Services are placed in Regions and AZs, and networks are split into subnets with clear rules.
- High availability comes from removing single points of failure and using multiple AZs.
- Caching, load balancing, and Auto Scaling help the system handle changing demand.
- Every design decision involves a tradeoff, and good architects make those tradeoffs deliberately.