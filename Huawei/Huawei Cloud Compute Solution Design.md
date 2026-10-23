# Huawei Cloud Compute Solution Design

**Level:** Beginner
**What you will do:** Learn the main compute services, choose the right one for a real case, and check your understanding with short questions.

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. Name the main Huawei Cloud compute services and explain when to use each one.
2. Read an instance name such as `c6.2xlarge.2` and choose an instance family for a workload.
3. Decide between a custom image, a startup script, or a hybrid approach when launching a server.
4. Match a storage service to a compute workload.
5. Apply the five pillars of compute design to a simple architecture.

---

## Running Example: The ShopFast Online Store

Throughout this lecture we will design the infrastructure for a small online store called **ShopFast**. We start simple and add parts as the business grows.

| Stage | What ShopFast needs |
|---|---|
| Day 1 | One web server to host the website |
| Growth | Two web servers so the site stays up if one fails |
| Scale | Shared uploads, a database, product images, and backups |

Keep ShopFast in mind. Every concept in this lecture answers a question ShopFast will face.

---

## Part 1: The Compute Options

Huawei Cloud offers compute in four families. Think of them like different types of housing.

| Service | Analogy | What it is | Typical use |
|---|---|---|---|
| **ECS** (Elastic Cloud Server) | An apartment in a shared building | A virtual machine you can scale up or down | Websites, business apps, most workloads |
| **BMS** (Bare Metal Server) | Owning a whole house | A full physical server with no virtualization | Large databases (e.g., Oracle, SAP HANA), high-performance computing |
| **DeH** (Dedicated Host) | Renting an entire building | A physical host reserved only for you, where you place your own VMs | Strict compliance, bring-your-own-license software |
| **CCE** (Cloud Container Engine) | A building manager for many apartments | A managed Kubernetes cluster | Microservices, many containers |
| **CCI** (Cloud Container Instance) | Booking a hotel room | Containers run without you managing servers | Short jobs, CI/CD pipelines, sudden traffic spikes |
| **FunctionGraph** | A vending machine | Code that runs only when an event triggers it | Webhooks, scheduled tasks, image processing |

**Quick check:** ShopFast's first website is a standard web application. Which service should it start on, and why?

---

## Part 2: Virtual vs. Physical

The main difference between ECS and BMS is whether a **hypervisor** (virtualization software) sits between your operating system and the hardware.

```
ECS (virtual)                         BMS (physical)
+-----------------------+             +-----------------------+
| VM 1        | VM 2    |             |                       |
| your OS     | other   |             |  Your OS runs         |
|             | customer|             |  directly on the      |
+-----------------------+             |  hardware             |
| Hypervisor            |             |                       |
+-----------------------+             +-----------------------+
| One shared physical   |             | One physical server,  |
| server                |             | used only by you      |
+-----------------------+             +-----------------------+
```

- **ECS:** Many customers share one physical server. Each gets a virtual machine. Flexible and cost-effective.
- **BMS:** The whole physical server is yours. There is no hypervisor, so performance is the highest. A hardware card called the **SDI card** handles networking and storage work.
- **DeH:** The whole physical host is yours, but you still run VMs on it. Useful when you need to control where VMs are placed.

**Key idea:** An ECS is a *virtual* machine. A BMS is a *physical* machine. From your point of view, both are normal servers you can log in to.

---

## Part 3: Choosing an Instance

### 3.1 Reading an instance name

Take the name `c6.2xlarge.2`. It has four parts:

| Part | Value | Meaning |
|---|---|---|
| Family | `c` | Compute-optimized |
| Generation | `6` | 6th hardware generation |
| Size | `2xlarge` | 8 vCPUs |
| Ratio | `.2` | 2 GB of RAM per vCPU |

**Worked example:** `c6.2xlarge.2` has 8 vCPUs, and 8 × 2 GB = **16 GB of RAM**.

> **Note:** Memorize how to read the name. Always check the exact specifications in the official Huawei Cloud documentation before you choose an instance.

### 3.2 Matching a family to a workload

| Workload type | Family examples | RAM : vCPU ratio | Good for |
|---|---|---|---|
| General purpose | t6 | Balanced | Small websites, dev/test, small databases |
| Compute-optimized | c6, c7 | 2 : 1 | Batch jobs, busy web APIs, video encoding |
| Memory-optimized | m6, m7 | 8 : 1 | Redis, Memcached, SAP, large caches |
| Ultra-high I/O | i3, i7 | Varies | Fast local storage for Cassandra, MongoDB, Hadoop |
| GPU / AI | g5, p2v, Ai3 | Varies | AI training and inference, 3D rendering |

**Quick check:** ShopFast's product search keeps a large in-memory cache of product data. Which family fits best, and why?

---

## Part 4: Starting a Server

When you launch a server, you choose how it gets its software. There are three options:

1. **Custom image:** Software is already installed in the image. It starts very fast, but you must build a new image every time the software changes.
2. **Startup script:** The server installs software when it boots. It is flexible, but it starts slowly and needs scripting skill.
3. **Hybrid (recommended):** Use a base image with the operating system and common runtimes, plus a short script for settings that change often.

| | Custom image | Startup script | Hybrid |
|---|---|---|---|
| Speed | Fast | Slow | Fast |
| Flexibility | Low | High | High |
| Maintenance | Many images to manage | Script must handle errors | Balanced |
| Can log in right away? | Yes | No, only after the script finishes | Yes, basic access first |

**Trade-offs to remember:**
- A custom image is quick, but changes are slow to deploy.
- A startup script is easy to change, but the server takes longer to be ready, and a script error can leave it half-configured.
- The hybrid approach gets most of the speed of an image and most of the flexibility of a script.

### 4.1 Writing a startup script

- **Linux:** The first line must be `#!/bin/bash`. Huawei Cloud runs it with Cloud-Init.
- **Windows:** Wrap PowerShell commands in `<powershell>` and `</powershell>` tags. Huawei Cloud runs them with Cloudbase-Init.
- **Large scripts:** Store the script in an Object Storage Service (OBS) bucket, and add a short command to the startup data that downloads and runs it.

> **Tip:** Keep scripts short, and make sure they are safe to run more than once.

**Quick check:** ShopFast changes its homepage banner every week. Which option should it use, and why?

---

## Part 5: Storage Services

A server can use storage in different ways. Huawei Cloud offers four main services:

| Service | Type | Best for | Watch out for |
|---|---|---|---|
| **EVS** (Elastic Volume Service) | Block disk attached to a server | System disk, database files | Normally attached to one server at a time |
| **Local disk** | Disk inside the physical host | Temporary data, caches, swap space | Data is lost if the host fails |
| **SFS** (Scalable File Service) | Shared network folder (NFS/CIFS) | Shared uploads across many servers | Slower than a local disk |
| **OBS** (Object Storage Service) | Files accessed over HTTP/HTTPS | Product images, backups, data lakes | Not a disk you can install software on |

**Durability:** EVS, SFS, and OBS all store data redundantly across hardware, so data is protected against single-hardware failures. Check the exact figures in the official documentation.

**Quick check:** Which storage should ShopFast use for:
1. The operating system disk of each web server?
2. Product photos that every web server must show?
3. A session cache that can be rebuilt if lost?

---

## Part 6: Designing for the Real World: The Five Pillars

Good compute design balances five goals. Each pillar includes a ShopFast example.

### 6.1 Security
- Place workloads in a **VPC subnet**, and use **security groups** (stateful firewall rules) to control traffic.
- Use **SSH key pairs** for Linux servers instead of passwords.
- Encrypt disks with **KMS**. Only attach an **Elastic IP (EIP)** to servers that need public access.
- Use **Host Security Service (HSS)** to detect intrusions and scan for vulnerabilities.

*ShopFast:* Only the load balancer gets a public IP. The web servers and database sit in private subnets.

### 6.2 Reliability
- Spread servers across **Availability Zones (AZs)** behind an **Elastic Load Balancer (ELB)**.
- Use **anti-affinity server groups** so servers run on different physical hardware.
- Back up automatically with **Cloud Backup and Recovery (CBR)**.

*ShopFast:* One web server is in AZ 1 and one is in AZ 2. If AZ 1 has a problem, the site keeps running.

### 6.3 Performance
- Choose the right family for the job (for example, memory-optimized for caches).
- Choose a disk type that gives the IOPS and throughput you need.
- Monitor CPU, memory, and disk with **Cloud Eye**.

*ShopFast:* During a sale, traffic spikes. Cloud Eye alerts the team before customers notice slow pages.

### 6.4 Cost Optimization
Think of cost as a cycle:

1. Pick the right instance.
2. Right-size it so you do not overpay.
3. Choose the right billing mode.
4. Use **Auto Scaling (AS)** to add or remove servers with demand.
5. Stop idle servers when they are not needed.
6. Monitor with Cloud Eye, then repeat.

- **Right-size:** A common guideline is to keep average CPU use around 40% to 70%. Much lower means you are wasting money. Much higher means there is no room for spikes.
- **Billing:** Pay-per-use suits unpredictable work. Monthly or yearly plans suit steady work.

> **Important billing rule:** Stopping an ECS stops its compute charges, but attached EVS disks and EIPs still cost money until you delete them.

*ShopFast:* Staging servers are stopped every night and on weekends.

### 6.5 Operations and Maintenance
- Patch the operating system on a regular schedule.
- Send logs to **Log Tank Service (LTS)** for alerts and audits.
- Manage infrastructure as code with **Terraform** or **Resource Formation Service (RFS)**, so servers are built the same way every time.

*ShopFast:* The whole setup is written as a Terraform template, so a new environment takes minutes instead of days.

---

## Part 7: Putting It All Together: ShopFast Final Architecture

```
                        Internet
                           │
                           ▼
              EIP (public IP) ──► Anti-DDoS / WAF
                           │
                           ▼
                Elastic Load Balancer (ELB)
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
      AZ 1 (Zone 1)                 AZ 2 (Zone 2)
   Subnet 192.168.1.0/24         Subnet 192.168.2.0/24
   ECS: Web App 1                ECS: Web App 2
   Encrypted EVS disk            Encrypted EVS disk
            │                             │
            └──────────────┬──────────────┘
                           ▼
          Shared services (used by both zones)
          • SFS: user uploads
          • OBS: product images and backups
          • CBR: automatic backups
          • Managed database (RDS) in a private subnet

   Anti-affinity group: keeps Web App 1 and Web App 2
   on separate physical hardware.
```

**How to read this diagram:**
1. Traffic enters from the internet through the public IP and the firewall.
2. The load balancer spreads requests across two web servers.
3. The two servers are in different AZs, and the anti-affinity group keeps them on separate physical hardware.
4. Shared data lives in SFS or OBS, and backups run through CBR.

---

## Part 8: Quiz

Try these before the lecture ends. Answers will be discussed in class.

**Q1 (True/False):** An ECS is a virtual machine, and a BMS is a physical machine.

**Q2 (Single choice):** Which instance type is most suitable for a high-performance database?
- A. General computing-plus
- B. Ultra-high I/O
- C. GPU-accelerated
- D. AI-accelerated

**Q3 (Multiple choice):** Which statements about server initialization are correct?
- A. Starting from an image is fast, but running a script is slow.
- B. If the software changes often, an image is the better choice.
- C. Writing startup scripts requires strong technical skill.
- D. You cannot log in to the server until the startup script finishes.

**Q4 (Scenario):** Two ShopFast servers must both read and write customer uploads. Which storage should you use?

**Q5 (Scenario):** A staging server is not needed on weekends. What happens to the bill if you stop it?

---

## Glossary

| Term | Meaning |
|---|---|
| **AZ** | Availability Zone: a separate data center within a region |
| **AS** | Auto Scaling: adds or removes servers based on demand |
| **BMS** | Bare Metal Server |
| **CBR** | Cloud Backup and Recovery |
| **CCE / CCI** | Cloud Container Engine / Cloud Container Instance |
| **DeH** | Dedicated Host |
| **ECS** | Elastic Cloud Server: a virtual machine |
| **EIP** | Elastic IP: a public IP address |
| **ELB** | Elastic Load Balancer |
| **EVS** | Elastic Volume Service: block storage disks |
| **HSS** | Host Security Service |
| **KMS** | Key Management Service |
| **LTS** | Log Tank Service |
| **OBS** | Object Storage Service |
| **RFS** | Resource Formation Service |
| **SDI** | Smart Driver Interface: a hardware card that offloads networking and storage work |
| **SFS** | Scalable File Service: a shared network file system |
| **VPC** | Virtual Private Cloud: your isolated network |

---

## Summary

- **Compute options:** ECS for most workloads, BMS for maximum performance, DeH for compliance, containers for microservices, and FunctionGraph for event-driven code.
- **Instance names** tell you the family, generation, size, and RAM per vCPU.
- **Launching a server:** Use a custom image for speed, a script for flexibility, or a hybrid of both.
- **Storage:** EVS for disks, local disk for temporary data, SFS for shared files, OBS for objects and backups.
- **Design:** Apply the five pillars: security, reliability, performance, cost, and operations.

---

*This handout is based on Huawei Cloud's compute solution materials. Specifications and prices change, so always confirm current details in the official Huawei Cloud documentation.*