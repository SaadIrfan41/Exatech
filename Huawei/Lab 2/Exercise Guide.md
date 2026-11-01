# High-Performance Network Solution: Student Guide

## What is this lab about?

In this lab you will build a small cloud network for a real website, the Discuz! forum. You will not just click through a setup wizard. You will decide **where each piece lives**, **who can talk to whom**, and **how traffic gets in and out**. These are the same decisions cloud engineers make every day when they design production systems.

By the end of the lab you should be able to:

- Split a cloud network into isolated subnets and explain why
- Use security groups to control which resources can reach each other
- Give private servers internet access (outbound) and make public services reachable (inbound)
- Connect two separate networks privately with VPC peering
- Use private DNS so people can use names instead of IP addresses

## Why do we design networks this way?

Imagine a company that runs a website and a database. If you put everything in one open network, anyone on the internet could try to reach the database directly. That is a serious security risk.

Good cloud design follows a few principles:

1. **Separate by role.** The web server and the database sit in different subnets.
2. **Expose as little as possible.** Only the web server faces the internet. The database has no public address.
3. **Allow only what is needed.** The database accepts connections only from the web server, and only on the database port.
4. **Control administrative access.** Engineers reach the private network through one controlled entry point, called a jump server, rather than connecting to every machine directly.

This lab teaches all four principles by building them.

## The architecture

| Component | Purpose |
|---|---|
| **vpc-primary** | The main private network for the website |
| **subnet-web** (192.168.1.0/24) | Holds the web server `ecs-web` |
| **subnet-db** (192.168.2.0/24) | Holds the database. Created in Part 1 |
| **ecs-web** | The virtual machine running Discuz! |
| **rds-discuz** | A managed MySQL database |
| **vpc-om** (172.16.0.0/16) | A separate network used only by administrators |
| **ecs-om** | The jump server that administrators log in to |
| **EIP** | A public IP address that lets the internet reach a server |
| **NAT Gateway** | A device that translates addresses so private servers can reach the internet and vice versa |
| **VPC peering** | A private link between two VPCs |
| **Private DNS zone** | A name-to-address lookup that works only inside your VPC |

A simple picture of the traffic flow:

```
Internet ──► NAT Gateway (DNAT) ──► ecs-web ──► rds-discuz
                 ▲                     ▲
                 │                     │ (peering, private)
ecs-web ──► NAT Gateway (SNAT) ──►     │
                                  ecs-om (admin jump server)
```

## Key concepts explained

**VPC (Virtual Private Cloud):** Your own isolated network inside the cloud. Nothing outside can reach it unless you allow it.

**Subnet:** A smaller range of addresses inside a VPC. Subnets let you group resources by purpose, such as web or database.

**Security group:** A firewall attached to a resource. It lists which traffic is allowed in and out. In this lab, `sg-db` allows MySQL traffic only from `sg-web`.

**EIP (Elastic IP):** A public IP address you can attach to a server so it is reachable from the internet.

**SNAT (Source NAT):** Lets private servers *send* traffic out to the internet. The outgoing traffic appears to come from the public IP. Think of it as "server reaches out."

**DNAT (Destination NAT):** Lets outside traffic *reach in* to a private server. Requests sent to the public IP on a port are forwarded to the server. Think of it as "outside reaches in."

**VPC peering:** A direct private connection between two VPCs. Peering does not work automatically. You must also add routes so each network knows how to send traffic to the other.

**Route table:** A list of rules that tells traffic where to go. "To reach 172.16.0.0/16, send traffic through the peering connection."

**Jump server (bastion host):** A single, tightly controlled machine that administrators use to reach the rest of the private network. It reduces the number of doors into your system.

**Private DNS:** Lets you assign a readable name, such as `www.abc.com`, to a private IP address. The name works only inside the VPC you attach it to.

## Scenario and requirements overview

**The scenario:** A company runs the Discuz! forum website. The website is already deployed on a web server (`ecs-web`) that has a public IP, but it is not connected to a database yet. Your job is to finish the network design so the website is secure, reachable by visitors, and manageable by administrators.

**What you need to do, in order:**

1. **Part 1:** Create a private subnet and firewall group for the database, buy a managed MySQL database, and install Discuz! so it connects to that database.
2. **Part 2:** Remove the public IP from the web server to prove it cannot reach the internet, then build a NAT gateway with SNAT and DNAT rules so the site works again through the gateway.
3. **Part 3:** Create a separate admin network with a jump server, connect it to the website network with VPC peering, add the routes and firewall rule, and confirm the admin server can reach the web server privately.
4. **Part 4:** Create a private DNS name for the web server and confirm the admin server can resolve it.

**What you need before starting:** Access to the lab environment with the provided IAM account, a basic understanding of VPCs, subnets, security groups, and DNS, and the lab's region set to AP-Singapore for every resource. Resources must be created exactly as specified, since unlisted or misplaced resources may be reclaimed.

## Step-by-step walkthrough

### Part 1: Basic environment configuration

**Goal:** Build the database side of the system and get the website running.

**Step 1: Create `subnet-db` and `sg-db`**
- *What you do:* Create a new subnet for the database in `vpc-primary`. Create a security group `sg-db` and allow MySQL (port 3306) into it. Change its source from an open range to `sg-web`.
- *Why:* The database gets its own subnet, and only the web server can reach it. Even if someone gets onto the network, they cannot connect to the database from anywhere else.

**Step 2: Buy an RDS database instance**
- *What you do:* Create a MySQL 5.7 instance named `rds-discuz` in `subnet-db`, protected by `sg-db`. Choose a primary and standby setup across two availability zones.
- *Why:* A managed database handles backups, patching, and failover for you. The primary/standby setup keeps the database running if one zone fails.

**Step 3: Install Discuz! and connect it to the database**
- *What you do:* Open the Discuz! installer through the web server's public IP. Enter the database address and credentials, then complete the installation and log in as administrator.
- *Why:* This confirms that the web server can reach the database through the private network you built. Successful login means the application tier and data tier are talking.

### Part 2: Internet access with EIP and NAT Gateway

**Goal:** Make the website reachable from the internet in a controlled way.

**Step 1: Remove the EIP and test**
- *What you do:* Unbind the public IP from `ecs-web` and try to load the website.
- *Why:* This is a deliberate experiment. The site stops working, which proves that the server has no route to or from the internet without a public address.

**Step 2: Create a public NAT gateway**
- *What you do:* Create `nat-web` in `vpc-primary`, attached to `subnet-web`.
- *Why:* The NAT gateway is the bridge between the private network and the internet. The web server stays private, and the gateway handles the crossing.

**Step 3: Add an SNAT rule**
- *What you do:* Create a rule that applies to the whole `subnet-web` range and uses the public IP.
- *Why:* This lets the web server send outbound requests, such as software updates, while keeping its private address hidden.

**Step 4: Add a DNAT rule**
- *What you do:* Map the public IP on port 80 to `ecs-web` on port 80.
- *Why:* This lets visitors from the internet reach the website, even though the server itself has no public address.

**Step 5: Verify**
- *What you do:* Refresh the browser and confirm that the Discuz! homepage loads.
- *Why:* Your traffic now flows through the NAT gateway. Visitors reach the site, and the server stays private.

### Part 3: Admin access with VPC peering

**Goal:** Let administrators reach the website's private address without exposing it to the internet.

**Step 1: Create `vpc-om`, `subnet-om`, and `sg-om`**
- *What you do:* Create a second VPC for administrators, with its own subnet and security group.
- *Why:* Admin access lives in a separate network. If the admin network is compromised, the attacker still has to pass through the controlled path to reach the website.

**Step 2: Create the jump server `ecs-om`**
- *What you do:* Launch a server in `subnet-om` with no public IP.
- *Why:* This server becomes the single entry point for maintenance. Administrators log in to it through the cloud console.

**Step 3: Create the VPC peering connection**
- *What you do:* Connect `vpc-primary` and `vpc-om` with `peering-web`. Add a route in each VPC's route table that points to the other VPC's address range, with the peering connection as the next hop.
- *Why:* The peering connection creates the link, but traffic only follows routes. Without the routes, packets have nowhere to go.

**Step 4: Allow the admin group into the web firewall**
- *What you do:* Add a rule to `sg-web` that allows all traffic from `sg-om`.
- *Why:* The security group is the final gatekeeper. Even with a route in place, the web server accepts connections only from sources you have explicitly allowed.

**Step 5: Test connectivity**
- *What you do:* From `ecs-om`, ping the private IP address of `ecs-web`.
- *Why:* A successful ping proves all three layers work together: the peering link, the routes, and the firewall rule.

### Part 4: Friendly names with private DNS

**Goal:** Let administrators use a name instead of an IP address.

**Step 1: Create a private zone**
- *What you do:* Create a private DNS zone named `www.abc.com` and attach it to `vpc-om` only.
- *Why:* A private zone is visible only inside the attached VPC. The name is useful for admins but invisible to the public internet.

**Step 2: Add an A record**
- *What you do:* Map `www.abc.com` to the private IP address of `ecs-web`.
- *Why:* An A record connects a name to an address. When systems grow, you can change the IP behind a name without retraining every person who uses it.

**Step 3: Verify**
- *What you do:* From `ecs-om`, ping `www.abc.com`.
- *Why:* Success confirms that DNS resolution works inside the private network.

## FAQ: Why can't I create an Enterprise Router attachment?

The lab's FAQ points to an important lesson. An Enterprise Router is a hub that connects many VPCs at once. When you attach a VPC to it with **Auto Add Routes** enabled, the platform adds routes for all private address ranges to that VPC's route table.

If a VPC peering connection still exists, its routes overlap with the router's routes, and the attachment fails. **You must delete the peering connection before creating the attachment.** Once it is removed, its routes are removed automatically.

The lesson: cloud networks are controlled by route tables, and two mechanisms that route to the same destination will conflict. Plan your routes before you change your architecture.

## Review questions

1. Why does the database have no public IP address?
2. What is the difference between SNAT and DNAT? Give an example of each from this lab.
3. Why does VPC peering need route table entries to work?
4. What would happen if `sg-db` allowed MySQL traffic from anywhere?
5. Why is a jump server safer than giving every administrator direct access to every machine?
6. Why must you delete a VPC peering connection before attaching the VPC to an Enterprise Router?

## Key takeaways

- **Isolate by role.** Put the web tier and data tier in separate subnets.
- **Restrict by default.** Allow only the traffic that is needed, from the sources that need it.
- **Control the doors.** Use NAT gateways for internet traffic and a jump server for administration.
- **Routes and firewalls both matter.** A connection needs a path (routes) and permission (security groups).
- **Names beat addresses.** Private DNS makes systems easier to operate as they grow.