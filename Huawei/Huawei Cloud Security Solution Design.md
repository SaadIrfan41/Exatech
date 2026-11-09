# Huawei Cloud Security Solution Design

**Level:** Beginner
**Prerequisites:** Compute, Storage, Network, and Database lectures
**What you will learn:** How security works in layers, who is responsible for what, and which Huawei Cloud service protects each part of a system.

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. Explain defense in depth, the idea of using several layers of protection.
2. Explain the shared responsibility model: what Huawei Cloud secures and what you secure.
3. Compare security groups and network ACLs.
4. Explain how Anti-DDoS, AAD, and WAF protect a website.
5. Explain how HSS protects servers, containers, and web pages.
6. Explain how IAM, CBH, and least privilege control who can do what.
7. Explain how CSMS, DEW, and CCM protect secrets, data, and certificates.
8. Explain how CTS and SecMaster help you audit and respond to threats.

---

## Running Example: ShopFast

ShopFast is the online store from our earlier lectures. It has:
- Web servers behind a load balancer
- An order database
- Product images in OBS
- Staff who manage the system

Every security service in this lecture protects some part of ShopFast.

---

## Part 1: Defense in Depth

**Defense in depth** means using several layers of protection. If one layer fails, another still stops the attack.

Think of a bank. It has a locked gate, a security guard, a locked door, and a safe. A thief who gets past the gate still faces the door and the safe.

```
Internet and users
        │
        ▼
┌────────────────────────────────────────┐
│ 1. Access layer    Anti-DDoS, AAD      │  Stop floods of traffic
├────────────────────────────────────────┤
│ 2. Service layer   WAF, HSS, ECS/BMS   │  Stop web attacks, protect servers
├────────────────────────────────────────┤
│ 3. Data layer      DEW, CCM, DBSS,     │  Encrypt and protect data
│                    RDS, EVS, OBS, SFS  │
├────────────────────────────────────────┤
│ 4. Access control  CBH, IAM            │  Control who can log in and act
├────────────────────────────────────────┤
│ 5. Audit           CTS, SecMaster      │  Record and respond to events
└────────────────────────────────────────┘
```

**ShopFast example:** A flood of fake traffic hits the website. Anti-DDoS absorbs most of it. Some attack requests get through, and WAF blocks them. An attacker who gets into a web server still cannot read the database, because the data is encrypted and the database accepts only the web tier.

---

## Part 2: Shared Responsibility

Security is shared between Huawei Cloud and you. Think of it as a building where the landlord locks the building, and you lock your own apartment.

| Area | Huawei Cloud is responsible for (security **of** the cloud) | You are responsible for (security **in** the cloud) |
|---|---|---|
| Physical facilities | Data centers, power, cooling, regions, AZs | (none) |
| Hardware and hypervisors | Servers, storage hardware, networks | (none) |
| Platform services | The security of the managed platform | How you configure it |
| Operating system | (not Huawei Cloud for ECS) | Patches, settings, users |
| Network rules | The network service itself | Which ports and sources you allow |
| Application | The platform's own applications | Your code and custom settings |
| Data | Storage hardware and the platform | Encryption, backups, who can read the data |
| Identity | The IAM service | Which users get which permissions |

**Key idea:** Huawei Cloud makes sure the building is safe. You decide which doors to lock inside it.

**ShopFast example:** Huawei Cloud keeps the data center secure. ShopFast must still choose a strong admin password, close unused ports, and decide who can read the order database.

---

## Part 3: Network Access Control

Two services control network traffic inside a VPC. They work at different levels.

### 3.1 Security groups (instance level)

A **security group** is a firewall around an instance, such as an ECS. It decides which traffic may reach or leave that instance.

- **Stateful:** if the instance sends a request out, the reply is allowed back in automatically.
- **Allow rules:** you normally write rules that allow traffic. Newer configurations also support deny rules.
- **Default:** inbound traffic from outside is denied unless you allow it.

**ShopFast example:** The web server's security group allows port 443 (HTTPS) from anywhere. The database's security group allows port 3306 (MySQL) only from the web servers' security group.

### 3.2 Network ACLs (subnet level)

A **network ACL** is a firewall around a whole subnet. It applies to every instance in that subnet.

- **Stateful:** replies to allowed requests are allowed through.
- **Allow and deny rules:** you can block a specific address for the whole subnet.
- **Default:** all inbound and outbound traffic is denied until you add rules.
- **Priority:** each rule has a number. A smaller number is checked first.

**ShopFast example:** The database subnet's network ACL blocks all traffic from one suspicious IP address, even if a security group would have allowed it.

### 3.3 Comparison

| Feature | Security group | Network ACL |
|---|---|---|
| Protects | Instances | Subnets |
| Mandatory? | Yes, every instance needs one | Optional |
| Allow and deny rules | Mainly allow | Allow and deny |
| Stateful | Yes | Yes |
| Default | Deny inbound | Deny inbound and outbound |
| Typical use | Per-application rules | Block whole ranges or add a second layer |

**Order:** Traffic is checked against the network ACL first, then against the security group. Using both gives you two layers.

**Quick check:** Which one would you use to block one attacker's address from the whole database subnet? *(Answer: the network ACL.)*

---

## Part 4: Protection Against Attacks on the Website

### 4.1 Anti-DDoS

A **DDoS attack** floods a website with so much traffic that real customers cannot reach it.

**Basic Anti-DDoS** is included automatically. It filters attack traffic at the network level (layer 4) for your public IP addresses, without interrupting service.

**Scrubbing (how it works):**
1. Traffic reaches the detection center.
2. Normal traffic goes straight to your server.
3. Attack traffic is sent to a scrubbing center, which cleans it.
4. Clean traffic is sent on to your server.

### 4.2 Advanced Anti-DDoS (AAD)

**AAD** is a paid service for larger attacks. Your public traffic is routed through AAD nodes, which filter both layer 4 (network) and layer 7 (application) attacks.

**Example:** SYN floods and large UDP floods are layer 4 attacks. AAD filters them before they reach ShopFast's load balancer.

### 4.3 Web Application Firewall (WAF)

**WAF** inspects the content of web requests. It works at layer 7, which means it reads the web request itself.

WAF blocks:
- **SQL injection:** an attacker types SQL commands into a form to read the database.
- **Cross-site scripting (XSS):** an attacker injects a script into a page.
- **OS command injection**
- **CC attacks:** many requests aimed at one page to overload it.
- **Malicious bots**

WAF also hides the real web servers. Traffic goes through WAF first, and WAF forwards clean traffic to the servers using its own IP addresses.

**Why security groups are not enough:** a security group checks only IP addresses and ports. A malicious SQL command arrives on port 443, which is allowed, so the security group lets it through. WAF reads the content and blocks it.

### 4.4 The full path

```
Customer ──► CDN ──► AAD (layer 4 and 7 DDoS) ──► WAF (web attacks)
                                                         │
                                                         ▼
                                              Load balancer ──► Web servers
                                                                  │
                                                                  ▼
                                                      Database (private subnet)
```

**ShopFast example:** An attacker sends a SQL injection through the search box. WAF sees the SQL command and blocks it. The database never receives the request.

**Quick check:** A flood of 10 Gbps of junk traffic hits ShopFast's public IP. Which service handles it first, and why not WAF?

---

## Part 5: Host and Workload Security (HSS)

**Host Security Service (HSS)** protects servers, including ECS, BMS, and containers, even across cloud and on-premises systems.

| Capability | What it does | ShopFast example |
|---|---|---|
| **Server security** | Scans for vulnerabilities, detects brute-force login attempts, detects malware and ransomware | Detects repeated SSH password guesses and blocks the source |
| **Container security** | Audits container images, isolates running containers, detects container escape attempts | Scans the product-catalog container image before deployment |
| **Web tamper protection** | Locks web directories and detects changes to web pages in memory | Stops an attacker from defacing the ShopFast homepage |

**Why it matters:** HSS works on the server itself, so it can see problems that network firewalls cannot, such as malware running inside the operating system.

---

## Part 6: Who Can Do What: IAM and CBH

### 6.1 Identity and Access Management (IAM)

**IAM** controls who can log in to the Huawei Cloud console and what they can do there.

Key ideas:
- **Users and groups:** people are placed in groups, such as "Developers" or "Auditors."
- **Policies:** rules that allow or deny actions, for example "allow read-only access to OBS."
- **Least privilege:** give each person only the permissions they need.

**How IAM decides:**
1. If any rule explicitly **denies** the action, the answer is **deny**.
2. If a rule explicitly **allows** it, the answer is **allow**.
3. If no rule matches, the answer is **deny**.

**ShopFast example:** The accountant's group can read invoices but cannot delete them. A deny rule on the production database blocks everyone from deleting it, even someone who has an allow rule for other resources.

**Best practices:**
- **Do not use the root account for daily work.** The root account has unlimited power. Create individual users.
- **Do not create access keys (AK/SK) for the root account.**
- **Turn on multi-factor authentication (MFA)** so a stolen password is not enough.
- **Set strong passwords** and session timeouts.

**Scope boundary:** IAM controls access to Huawei Cloud and its console. It does not control logins inside a Linux server or user accounts inside your application's database.

### 6.2 Cloud Bastion Host (CBH)

A **bastion host** is a controlled gateway for administrators. Instead of logging in to each server directly, administrators connect through CBH.

CBH:
- Controls who can reach each server
- Records every session
- Lets you replay what an administrator did

**ShopFast example:** A contractor needs to fix the database for one afternoon. Through CBH, the contractor gets access only to that database, and every command they type is recorded.

**Why it matters:** When something goes wrong, you can see who did what, and when.

---

## Part 7: Protecting Data, Secrets, and Certificates

### 7.1 Data Encryption Workshop (DEW)

**DEW** is the family of encryption and key services. It includes **KMS** (Key Management Service), which stores encryption keys.

Two kinds of encryption:
- **Server-side encryption:** the cloud encrypts data as it is stored.
- **Client-side encryption:** your application encrypts data before sending it.
- **Data in transit:** use HTTPS so data is encrypted while moving across the network.

**ShopFast example:** The EVS disk holding the order database is encrypted. If someone steals the disk, they cannot read it without the key.

### 7.2 Cloud Secret Management Service (CSMS)

Applications need passwords to reach databases. Storing those passwords in code is a serious risk. If the code is leaked, the passwords are leaked too.

**CSMS** stores secrets, such as database passwords, outside the code. The application asks CSMS for the password when it needs it.

```
Application ──► asks CSMS for the database password (using an IAM agency)
     │                       │
     │ ◄──────── returns password, short-lived ────────
     ▼
Database
```

**ShopFast example:** The web application no longer has the database password in its config file. It asks CSMS at startup.

**Key idea:** No password in the code means nothing to steal from the code.

### 7.3 Cloud Certificate Manager (CCM)

A **certificate** proves that a website is genuine and enables HTTPS. CCM manages certificates in two ways:

- **SSL Certificate Manager (SCM):** buys and installs public certificates for websites, WAF, load balancers, and DNS.
- **Private Certificate Authority (PCA):** issues private certificates for encrypting traffic between your own internal services.

**ShopFast example:** The shop's domain uses a public certificate from SCM, installed on the WAF. Customers see the padlock in their browser. Internal services talk to each other using certificates from PCA.

**Common mistake:** An expired certificate makes the website show a warning, and customers may leave. Track expiry dates.

---

## Part 8: Auditing and Responding to Threats

### 8.1 Cloud Trace Service (CTS)

**CTS** records every action taken on Huawei Cloud resources, such as creating an ECS, deleting a database, or changing a security group.

Each record shows:
- Who did it
- What they did
- When it happened
- From which IP address

Records can be sent to **LTS** (Log Tank Service) for real-time analysis, and to **OBS** for long-term storage.

**ShopFast example:** The database is deleted at 2 a.m. CTS shows which user deleted it, from which address, and when. The team can contact that user and restore from backup.

### 8.2 SecMaster

**SecMaster** is a security operations platform. It gathers information from HSS, WAF, AAD, CFW, CTS, and IAM into one console.

It helps with:
- **Asset inventory:** finds all cloud resources, including ones nobody has documented
- **Threat detection:** finds suspicious activity across services
- **Compliance reporting:** checks against standards such as ISO 27001, PCI-DSS, and MLPS
- **Automated response:** runs playbooks, such as blocking an IP address, as soon as a threat is detected

**ShopFast example:** SecMaster sees many failed logins from one address across HSS and CTS. It runs a playbook that blocks the address through the security group and notifies the team.

---

## Part 9: Putting It All Together

Here is one attack from start to finish.

**Attack:** Someone sends a SQL injection through a ShopFast search box, and tries repeated SSH logins to a web server.

| Step | Service | What happens |
|---|---|---|
| 1 | AAD | Filters the flood of junk traffic before it reaches ShopFast |
| 2 | WAF | Blocks the SQL injection in the search request |
| 3 | Security group | Blocks SSH from addresses that are not allowed |
| 4 | HSS | Detects the repeated SSH password guesses and blocks the source |
| 5 | CBH | Ensures administrators log in only through the controlled gateway |
| 6 | CTS | Records every action for investigation |
| 7 | SecMaster | Combines the alerts and runs the response playbook |

**Lesson:** No single service stops every attack. Together, they cover each layer.

---

## Summary

- **Defense in depth:** several layers, so one failure does not mean a breach.
- **Shared responsibility:** Huawei Cloud secures the platform. You secure your configuration, code, and data.
- **Security group:** instance-level firewall. **Network ACL:** subnet-level firewall.
- **AAD and Anti-DDoS:** stop floods. **WAF:** stops web attacks by reading content.
- **HSS:** protects the server, containers, and web pages.
- **IAM:** who can do what. Use least privilege and never use the root account for daily work.
- **CBH:** a controlled, recorded gateway for administrators.
- **DEW, CSMS, CCM:** encryption keys, secrets outside code, and certificates.
- **CTS and SecMaster:** record actions, then detect and respond to threats.

---

## Review Questions

1. What is defense in depth? Give one example from ShopFast.
2. Which is responsible for the physical security of the data center: you or Huawei Cloud?
3. Why is a network ACL useful even when you already have security groups?
4. A SQL injection goes through port 443. Why does a security group not stop it?
5. Why should ShopFast not use the root account for daily work?
6. Why is a database password stored in CSMS better than in the application's code?

---

*This handout is based on Huawei Cloud's security solution materials. Service features, limits, and billing can change, so confirm the details in the official documentation before class.*