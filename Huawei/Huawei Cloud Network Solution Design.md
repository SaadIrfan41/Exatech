# Huawei Cloud Network Solution Design

**Level:** Beginner
**Prerequisites:** Compute and Storage Solution Design lectures (ECS, EVS, SFS, OBS)
**What you will do:** Learn how to design a private network in Huawei Cloud, connect it to the internet and to an office, link networks together, and choose the right option for each job.

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. Explain what a VPC, a subnet, and a CIDR block are.
2. Calculate how many usable IP addresses a subnet has.
3. Choose between an EIP and a NAT gateway for internet access.
4. Compare IPsec VPN and Direct Connect for connecting an office.
5. Choose the right option for connecting VPCs: VPC Peering, Enterprise Router, VPC Endpoint, or Cloud Connect.
6. Explain the difference between public and private DNS.

---

## Running Example: The ShopFast Network

ShopFast now needs a network. We will build it step by step.

| Requirement | Network answer |
|---|---|
| Servers must be private and isolated | A VPC with subnets |
| Customers must reach the website | An EIP on the load balancer |
| Servers must download updates but stay private | A NAT gateway |
| The office must reach the servers securely | A VPN or Direct Connect link |
| A second VPC for the analytics team | VPC Peering |
| A disaster-recovery site in another region | Cloud Connect |
| Servers must reach OBS without public traffic | VPC Endpoint |

---

## Part 1: The Five Questions of Cloud Networking

Most network design comes down to five questions. Use this map to find the right service.

| Question | Services |
|---|---|
| How do I build a private network? | VPC, subnets, route tables |
| How do my servers reach the internet? | EIP, NAT Gateway |
| How do I connect my office? | IPsec VPN, Direct Connect |
| How do I link my networks together? | VPC Peering, Enterprise Router, VPC Endpoint, Cloud Connect |
| How do names turn into addresses? | Public DNS, Private DNS |

---

## Part 2: VPC, Subnets, and IP Addresses

### 2.1 What is a VPC?

A **Virtual Private Cloud (VPC)** is your own isolated network in Huawei Cloud. Servers inside one VPC can talk to each other privately. Servers in different VPCs cannot talk to each other until you connect them (Part 6).

**Single or multiple VPCs?**
- **One VPC** is simpler and fits a small team or a single application.
- **Multiple VPCs** make sense when teams, environments (development, testing, production), or departments need strict separation.

### 2.2 What is a subnet?

A **subnet** is a smaller section of the VPC's address range. Each subnet is placed in **one Availability Zone (AZ)**. To survive an AZ failure, put servers in subnets in two different AZs.

### 2.3 What is a CIDR block?

A **CIDR block** is an address range written as an IP address followed by a slash and a number, such as `192.168.0.0/22`. The number after the slash is the **prefix length**. It tells you how many bits are fixed:

- A **larger** prefix means a **smaller** range.
- `/22` gives 1,024 addresses. `/24` gives 256 addresses.

```
VPC CIDR 192.168.0.0/22  (1,024 addresses)
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ 192.168.0.0/24   │ 192.168.1.0/24   │ 192.168.2.0/24   │ 192.168.3.0/24   │
│ Subnet 1 (AZ 1)  │ Subnet 2 (AZ 2)  │ Subnet 3 (DB)    │ Subnet 4 (spare) │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

Each subnet inside the VPC range must not overlap with another subnet.

### 2.4 Usable addresses in a subnet

Every subnet reserves **five addresses** that servers cannot use. For `192.168.0.0/24`:

| Address | Role |
|---|---|
| `192.168.0.0` | Network address (start of the range) |
| `192.168.0.1` | Gateway address |
| `192.168.0.253` | System interface, used by the VPC for external communication |
| `192.168.0.254` | DHCP service address |
| `192.168.0.255` | Broadcast address |

**Worked example:**
- A `/24` subnet has 2^(32 − 24) = 2^8 = **256** addresses.
- Subtract the 5 reserved addresses: 256 − 5 = **251 usable addresses**.

> **Note:** The reserved addresses depend on your subnet settings, but there are always five.

**Quick check:** How many usable addresses does a `/26` subnet have? *(Hint: 2^(32 − 26) first.)*

---

## Part 3: Routes: How Traffic Finds Its Way

A **route table** tells traffic where to go. Each subnet uses a route table. Every VPC has a default route table. The system routes in it cannot be deleted. You can add your own routes, for example to send internet traffic through a NAT gateway or a firewall.

**ShopFast example:** The private database subnet has no route to the internet. Its route table only sends traffic to the other ShopFast subnets and to the office link.

---

## Part 4: Reaching the Internet

Servers can reach the internet in two ways.

### 4.1 Elastic IP (EIP)

An **EIP** is a static public IPv4 address. You attach it to an ECS, a load balancer, or a NAT gateway. It works like a personal phone number that anyone can call.

**Billing options** include pay-per-use, by bandwidth, by traffic, monthly or yearly plans, and shared bandwidth packages.

### 4.2 NAT Gateway

A **NAT gateway** lets many servers with private addresses share one public address. It works in two directions:

- **SNAT (outbound):** Private servers start connections to the internet, such as downloading updates. The internet sees only the public address.
- **DNAT (inbound):** A public port is mapped to one private server and port, so incoming requests reach the right machine.

**ShopFast example:** The web servers have private addresses. They use SNAT to download security updates. The public load balancer uses an EIP so customers can reach the site.

```
Private servers (no public IP)
    │  SNAT (outbound)
    ▼
NAT gateway ──► EIP ──► Internet
    ▲
    │  DNAT (inbound)
Internet ──► EIP port 443 ──► Web server 192.168.0.10:443
```

### 4.3 NAT gateway rules to know

- Each VPC can have **one** NAT gateway.
- Each subnet can be used in **one** SNAT rule.
- A public NAT gateway can have up to **200** DNAT rules.
- One EIP can be shared by SNAT and DNAT rules, except that an SNAT rule cannot share an EIP with a DNAT rule set to **All ports**.
- If a server has both an EIP and a NAT gateway, its traffic goes through the EIP.

> **Note:** Rules like these change over time. Check the current NAT Gateway documentation before teaching them.

**Quick check:** Why would ShopFast put its web servers behind a NAT gateway instead of giving each one an EIP?

---

## Part 5: Connecting the Office

Your office and your cloud network need a secure link. Huawei Cloud offers two options.

### 5.1 IPsec VPN

A **VPN** creates an encrypted tunnel over the public internet between your office gateway and a VPN gateway in your VPC.

- **Quick to set up:** Usually works straight away.
- **Bandwidth depends on the internet** and on the VPN gateway specification. Bandwidth limits differ between documentation versions, so check the current figure.

### 5.2 Direct Connect (DC)

**Direct Connect** is a dedicated physical line from your data center to Huawei Cloud.

- **One connection supports up to 100 Gbit/s.** Port types are 1GE, 10GE, 40GE, and 100GE.
- **Default maximum is 1000 Mbit/s.** A higher speed needs a 10GE or faster optical port.
- **Setup takes longer,** because the leased line must be installed by a carrier.
- **Best practice:** Use at least two connections in different locations, so one can back up the other.

### 5.3 Comparison

| | IPsec VPN | Direct Connect |
|---|---|---|
| Path | Public internet, encrypted | Private leased line |
| Latency | Varies with internet conditions | Lower and more consistent |
| Maximum bandwidth | Depends on VPN gateway specification | Up to 100 Gbit/s per connection |
| Setup time | Quick | Depends on the carrier |
| Good for | Testing, small offices, backup links | Large data transfers, strict performance needs |

**Quick check:** ShopFast needs a link for the office by next Monday, and the budget is small. Which option fits, and what would you add later?

---

## Part 6: Linking Networks Together

### 6.1 VPC Peering

**VPC Peering** connects two VPCs in the **same region** so their servers can talk privately.

- **Currently free** (check current pricing).
- **Address ranges must not overlap.** Two VPCs that both use `192.168.0.0/24` cannot be peered.
- **Not transitive.** If A is peered with B and B is peered with C, A cannot reach C. You need a peering between A and C too.

```
   VPC A ◄──── peering ────► VPC B ◄──── peering ────► VPC C

   VPC A cannot reach VPC C through VPC B.
   Add a direct A–C peering if they need to communicate.
```

### 6.2 Enterprise Router (ER)

An **Enterprise Router** is a central hub. Many VPCs and office links connect to it, and it shares routes between them. Use it instead of many peerings when you have many VPCs.

### 6.3 VPC Endpoint (VPCEP)

A **VPC Endpoint** gives private access to a cloud service, or to a private service in another VPC, without an EIP.

- **No EIP needed,** so no public exposure.
- **Each gateway supports up to 1 million concurrent connections.**

**ShopFast example:** Servers reach OBS through a VPC Endpoint, so product photos never travel over the public internet.

### 6.4 Cloud Connect (CC)

**Cloud Connect** links VPCs in **different regions** and can link office networks too.

- **VPCs with overlapping address ranges cannot be connected.**

**ShopFast example:** The disaster-recovery site runs in another region and connects to the main VPC through Cloud Connect.

### 6.5 Which one should I use?

| Scenario | Best choice |
|---|---|
| Two VPCs in one region | VPC Peering |
| Many VPCs and office links in one region | Enterprise Router |
| Private access to OBS or another service, without EIP | VPC Endpoint |
| VPCs in different regions | Cloud Connect |
| Small office link, quick setup | IPsec VPN |
| Large office link, strict performance | Direct Connect |

---

## Part 7: Names: Public and Private DNS

DNS turns names into addresses. There are two kinds.

### 7.1 Public DNS

Public DNS resolves names that people on the internet use, such as `www.shopfast.example`, to public IP addresses.

```
1. Customer types www.shopfast.example
2. The customer's device asks public DNS for the address
3. DNS returns the EIP
4. The device connects to the EIP and loads the site
```

### 7.2 Private DNS

Private DNS resolves internal names, such as `db.shopfast.internal`, to private addresses inside your VPC. Internal names never appear on the public internet.

```
1. Web server asks private DNS for db.shopfast.internal
2. Private DNS returns 192.168.2.10
3. The web server connects directly to the database
```

**ShopFast example:** Customers use public DNS for the website. The web servers use private DNS to find the database.

---

## Part 8: ShopFast Network Architecture

```
                          Internet
                             │
                       EIP (public IP)
                             │
                  Elastic Load Balancer
                             │
   ┌─────────────── VPC 192.168.0.0/22 (Region A) ───────────────┐
   │                                                              │
   │  AZ 1: 192.168.0.0/24          AZ 2: 192.168.1.0/24          │
   │  Web Server 1                  Web Server 2                  │
   │                                                              │
   │  DB subnet: 192.168.2.0/24  (no internet route)              │
   │  Database (private DNS: db.shopfast.internal)                │
   │                                                              │
   │  NAT gateway: outbound updates for private servers           │
   │  VPC Endpoint: private access to OBS                         │
   └──────────┬───────────────────────────┬───────────────────────┘
              │                           │
      VPN or Direct Connect        Cloud Connect
              │                           │
        Office network          Disaster-recovery VPC (Region B)
```

**How to read this:**
1. Customers reach the load balancer through an EIP.
2. Web servers sit in two AZs, and the database sits in a private subnet with no internet route.
3. Private servers use the NAT gateway for outbound updates.
4. The office connects through VPN or Direct Connect.
5. The disaster-recovery VPC in another region connects through Cloud Connect.

---

## Part 9: Quiz

Try these before the lecture ends. Answers will be discussed in class.

**Q1 (Single choice):** How many usable addresses does a `/24` subnet have?
- A. 254
- B. 251
- C. 256
- D. 250

**Q2 (Single choice):** VPC A is peered with VPC B, and VPC B is peered with VPC C. Can VPC A reach VPC C through this setup?
- A. Yes, because peering is transitive
- B. No, peering is not transitive
- C. Yes, if both VPCs use EIPs

**Q3 (Single choice):** Two VPCs both use `192.168.0.0/24`. Can they be peered?
- A. Yes
- B. No, their address ranges overlap

**Q4 (Single choice):** Private web servers need to download updates from the internet, but they must not have public addresses. Which service fits?
- A. VPC Endpoint
- B. NAT gateway (SNAT)
- C. Enterprise Router

**Q5 (Scenario):** ShopFast needs a disaster-recovery VPC in another region connected to its main VPC. Which service should you use?

**Q6 (Scenario):** Servers in a VPC must reach OBS privately, without an EIP. Which service should you use?

**Q7 (Scenario):** ShopFast needs a large, steady link for daily data transfers from its data center. Which option is the better fit, VPN or Direct Connect, and why?

---

## Glossary

| Term | Meaning |
|---|---|
| **AZ** | Availability Zone: a separate data center within a region |
| **CIDR block** | An IP address range written with a prefix length, such as `/24` |
| **Cloud Connect (CC)** | Links VPCs across regions |
| **DNAT** | Maps a public address and port to a private server |
| **Direct Connect (DC)** | A dedicated physical line from a data center to the cloud |
| **EIP** | Elastic IP: a static public IPv4 address |
| **Enterprise Router (ER)** | A central hub that connects many VPCs and office links |
| **NAT gateway** | Lets private servers share public addresses |
| **Prefix length** | The number after the slash in a CIDR block |
| **Private DNS** | Resolves internal names to private addresses |
| **Public DNS** | Resolves public names to public addresses |
| **Route table** | Rules that tell traffic where to go |
| **SNAT** | Lets private servers reach the internet through a shared public address |
| **Subnet** | A section of a VPC address range, placed in one AZ |
| **VPC** | Virtual Private Cloud: your isolated network |
| **VPC Peering** | A private link between two VPCs in the same region |
| **VPC Endpoint (VPCEP)** | Private access to services without an EIP |
| **VPN** | An encrypted tunnel over the internet |

---

## Summary

- A **VPC** is your private network, and **subnets** split it into parts placed in AZs.
- A **/24** subnet has **251** usable addresses after five reserved ones.
- **EIP** gives public access to one resource. **NAT gateway** lets many private servers share public access.
- **VPN** is quick and encrypted over the internet. **Direct Connect** is a dedicated, higher-performance line.
- **VPC Peering** works within one region and is not transitive. **Enterprise Router** handles many VPCs. **VPC Endpoint** gives private service access without an EIP. **Cloud Connect** links regions.
- **Public DNS** serves customers. **Private DNS** serves your servers.

---

*This handout is based on Huawei Cloud's network documentation. Prices, limits, and features change, so confirm current details in the official Huawei Cloud documentation before class.*