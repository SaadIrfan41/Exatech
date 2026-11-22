# Student Handout: Highly Elastic Service System

## 1. What this lab is about

In this lab you turn a single Discuz! forum server into a system that can grow and shrink with traffic. You will:

1. Connect the web server to a managed database (RDS), using a private subnet.
2. Put a load balancer (ELB) in front of the web server, so one public address serves all traffic.
3. Use Auto Scaling (AS) to add or remove web servers when CPU load changes.
4. Use Auto Scaling to change the bandwidth when inbound traffic grows.
5. Practise manual scaling, instance protection, changing server specifications and sending notifications.

**ShopFast example:** ShopFast's sale starts at 20:00 and the checkout servers slow down. Without elasticity, customers wait or get errors. With this lab's setup, the load balancer spreads requests across the servers, Auto Scaling adds a server when CPU stays high, and the bandwidth policy raises the network limit when traffic spikes. When the sale ends, extra servers are removed again.

| Stage | ShopFast equivalent | Lab section |
|---|---|---|
| Private database network | Orders stay away from the public internet | Section 1, steps 1–2 |
| Managed database | Checkout reads and writes orders in RDS | Section 1, step 2 |
| Load balancer | One public address spreads customers across servers | Section 2 |
| CPU-based scaling | More checkout servers during the sale | Section 3 |
| Bandwidth scaling | Bigger network pipe when traffic spikes | Section 4 |
| Maintenance | Manually add servers, protect key servers, get notified | Section 5 |

**Learning objectives**

1. Build a database in a private subnet and connect a web application to it.
2. Configure a load balancer and check that traffic reaches the backend servers.
3. Create an AS configuration and an AS group, and link them to the load balancer.
4. Create alarm-based scaling policies for CPU and bandwidth.
5. Generate load on purpose and confirm that scaling happens.

---

## 2. Key terms

- **ELB (Elastic Load Balance):** a service that receives requests on one address and forwards them to several servers.
- **Shared load balancer:** an ELB type that many users share. The lab uses this type.
- **Listener:** the rule that says which port the load balancer accepts traffic on (here TCP port 80).
- **Backend server group:** the list of servers that receive the forwarded traffic.
- **Weighted round robin:** a balancing method that takes turns between servers, giving more turns to servers with a higher weight.
- **EIP (Elastic IP):** a public IP address you can attach to a resource so it can be reached from the internet.
- **AS configuration:** a template that describes what a new server looks like: specification, image, disk and security group.
- **AS group:** the set of servers that Auto Scaling manages, with minimum, expected and maximum counts.
- **AS policy:** a rule that adds or removes servers. An alarm policy runs when a metric crosses a limit.
- **Cooldown period:** a waiting time after a scaling action during which no new scaling action starts.
- **Instance protection:** a setting that stops a chosen server from being removed by scale-in.
- **Image:** a saved copy of a server's disk. New servers are built from it.

---

## 3. Before you start

- Log in with the account given in the lab. Do not use your own cloud account.
- The lab text uses one password in several places. Use the password the lab provides, or choose your own and write it down somewhere safe.
- Use the **AP-Singapore** region for every resource, as the lab says. Resources in different regions cannot be connected to each other.
- Note the **private IP of ecs-web**, the **RDS private IP**, and the **EIP of elb-web** when you get them. You need them in later steps.
- Save your notes and screenshots as you go. The lab releases resources when the time runs out or when you exit.

---

## 4. Section by section

### Section 1: Basic environment configuration

**Overview:** The lab provides a VPC (`vpc-primary`), a subnet for web servers (`subnet-web`), and a server `ecs-web` with Discuz! installed. The server is not yet connected to a database. You add a database subnet, a database, and connect them.

---

#### Step 1: Create subnet-db

**What you do:** Open the VPC console, select `vpc-primary`, go to Subnets, and click Create Subnet. Enter:
- VPC: `vpc-primary`
- Name: `subnet-db`
- IPv4 CIDR block: `192.168.2.0/24`

**What the CIDR means:** `192.168.2.0/24` is a block of addresses. The `/24` means the first three numbers are fixed (`192.168.2`) and the last number can change, giving 256 addresses. The cloud reserves 5 of them, so 251 can be used.

**Why a separate subnet:** The database should not share a network with the public-facing web server. If the web server is attacked, the database still sits behind a second boundary.

**Example:** ShopFast keeps web servers in `subnet-web` and the orders database in `subnet-db`. You now have two subnets in the same VPC.

**Check:** The subnet list shows both `subnet-web` and `subnet-db`.

---

#### Step 2: Create sg-db and buy the RDS instance

**Part A: Create the security group**

**What you do:** In the VPC console, create a security group named `sg-db`. For **Template**, choose **Fast-add rule**, and for **Inbound Rules** select **MySQL (3306)**.

**What the template does:** It adds a rule for port 3306 with one click, so you do not type the port yourself. After creation, you change the source of this rule.

**Part B: Restrict the source**

**What you do:** Open `sg-db`, go to Inbound Rules, find the rule for TCP port 3306, and change the source from `0.0.0.0/0` to the **private IP of ecs-web**.

**What this means:** Only the web server can connect to the database on port 3306. Everyone else is blocked, even if they know the database address.

**Example:**

| Source | Port | Result |
|---|---|---|
| Private IP of ecs-web | 3306 | Allowed |
| 0.0.0.0/0 | 3306 | Not allowed in a real system |

**Part C: Buy the RDS instance**

**What you do:** Open the RDS console and click **Buy DB instance**. Use these values:

| Setting | Value | What it means |
|---|---|---|
| Billing Mode | Pay-per-use | You pay only while the database runs |
| Region | AP-Singapore | Must match your other resources |
| DB Instance Name | rds-web | The name you use to find the instance |
| DB Engine / Version | MySQL 5.7 | The database software the forum expects |
| DB Instance Type | Primary/Standby | Two copies, so one can take over if the other fails |
| Storage Type | Cloud SSD | Fast storage for the database |
| Primary AZ / Standby AZ | AZ5 / AZ3 | The two copies sit in different data centres |
| Time Zone | UTC+08:00 | The database's clock matches Asia time |
| Instance Class | Dedicated, 2 vCPUs, 4 GB | How much CPU and memory the database gets |
| Storage Space | 40 GB | How much disk space the database gets |
| Disk Encryption | Disable | Encryption is not needed for this lab |
| VPC / Subnet | vpc-primary / subnet-db | Puts the database in the private subnet |
| Database Port | 3306 | The port MySQL listens on |
| Security Group | sg-db | Allows only ecs-web to connect |
| Password | Set the lab password, or your own | The administrator password for the database |

**Why these choices:** The database is in a private subnet, protected by `sg-db`, and has a standby copy in another AZ. This is the same design you saw in the O&M lab.

**Watch out:** The database password is the root password of the database. If you lose it, you cannot recover it, so write it down.

---

#### Step 3: Install Discuz! and connect it to RDS

**What you do:**
1. In the ECS console, copy the **public IP (EIP)** of ecs-web.
2. Open a browser on the lab desktop and go to `http://EIP:80`. Click **I agree**.
3. The installer checks that folders are writable and that the needed functions exist. If everything passes, click **Next**.
4. Select **A new installation Discuz! X (Contain UCenter Server)** and click **Next**.
5. Enter the database settings:
   - **Database server:** the **private IP of rds-web** (copy it from the RDS console)
   - **Database password:** the root password you set for the database
   - **Admin password:** a password for the forum administrator `admin`
   - **Repeat password:** the same admin password
6. Wait for the installation to finish, then open `http://EIP:80` again.

**What is happening:** The installer connects from ecs-web to the database at the private IP, creates the forum tables, and stores the connection details on ecs-web.

**Why the private IP:** The connection stays inside the VPC, so the database is never exposed to the internet.

**Check:** If the installer says it cannot connect to the database, check the database IP, the root password, and the `sg-db` rule source.

---

### Section 2: Configuring ELB

**Overview:** Right now, ecs-web has its own public IP. In this section, the load balancer takes over the public address, and the server becomes a backend behind it.

---

#### Step 1: Unbind the EIP from ecs-web

**What you do:** In the ECS console, locate `ecs-web`, choose **More > Manage Network > Unbind EIP**, and click **Yes**.

**What this does:** It removes the public IP from the server. The server keeps its private IP and is still reachable inside the VPC.

**Why:** The load balancer needs a public address of its own. You will attach the freed EIP to the load balancer in the next step.

**Example:** ShopFast's public address now points to the load balancer, not to a single server. Customers always use the same address, even when the servers behind it change.

---

#### Step 2: Create the load balancer

**Part A: Buy the load balancer**

**What you do:** Open **Elastic Load Balance** and click **Buy Elastic Load Balancer**. Set:

| Setting | Value | What it means |
|---|---|---|
| Type | Shared load balancer | A shared, lower-cost type of load balancer |
| Billing Mode | Pay-per-use | You pay for use only |
| Region | AP-Singapore | Same region as the other resources |
| Name | elb-web | The name you use later |
| Network Type | Public IPv4 network | The load balancer can be reached from the internet |
| VPC | vpc-primary | The same network as the web servers |
| Frontend Subnet | subnet-web | The subnet where the load balancer listens |
| IPv4 Address | Automatically assign | The cloud picks a private address for the load balancer |
| EIP | Use existing | Attaches the EIP you freed in Step 1 |

Click **Next**, check the summary, and click **Submit**.

**Part B: Add a listener**

**What you do:** In the load balancer list, click **Add now** for elb-web. Set:
- Name: `listener-web`
- Frontend protocol: **TCP**
- Frontend port: **80**
- Access control: **All IP addresses**

**What a listener does:** It tells the load balancer "accept connections on port 80 from anyone".

**Part C: Create the routing policy and backend group**

**What you do:** Set:
- Backend server group: **Create new**, named `server_group-web`
- Backend protocol: **TCP**
- Load balancing algorithm: **Weighted round robin**

**What round robin means:** The load balancer sends each new request to the next server in the list. "Weighted" means a server with a higher weight gets more requests. The lab gives every server the same weight, so they share the load equally.

**Part D: Add the backend server**

**What you do:** Click **Add Backend Server**, select `ecs-web`, set **Backend port** to **80**, and click **OK**. Then click **Next: Confirm** and **Submit**.

**What this does:** The load balancer sends forwarded traffic to ecs-web on port 80, where Discuz! listens.

**Check:** In the load balancer list, elb-web shows as running.

---

#### Step 3: Verify the service

**What you do:** On the lab desktop, open a browser and go to `http://EIP:80`, where the EIP is now the one attached to elb-web.

**What you should see:** The Discuz! forum. The traffic reaches the server through the load balancer.

**Example:** This is the same as a shop's front door: the customer uses one address and never sees which back-room server handled the request.

---

### Section 3: Auto Scaling for compute resource scaling

**Overview:** Auto Scaling adds and removes web servers automatically. To do that, it needs a template for new servers, a group to manage them, and rules that decide when to act.

---

#### Step 1: Create an image of ecs-web

**What you do:** Open **Image Management Service** and click **Create Image**. Set:
- Type: **Create Image**
- Image type: **System disk image**
- Source: **ECS**, and select `ecs-web`
- Name: `image-web`
- Tick the image disclaimer agreement, click **Next**, then **Submit**.

**What an image is:** A copy of the server's disk, including Discuz! and its settings. New servers start from this copy, so they already run the forum.

**Why:** Without an image, Auto Scaling would create blank servers with no forum.

**Example:** It is like cloning a fully set-up checkout counter, so each new counter opens ready to serve customers.

**Check:** Under **Private Images**, `image-web` appears.

---

#### Step 2: Create an AS configuration

**What you do:** Open **Auto Scaling**, go to **Instance Scaling**, and click **Create AS Configuration**. Set:

| Setting | Value | What it means |
|---|---|---|
| Billing Mode | Pay-per-use | You pay for servers only while they run |
| Region | AP-Singapore | Same region as the other resources |
| Name | as-config-web | The name of the template |
| Configuration template | Create new template | Starts a new template |
| CPU architecture | x86 | The processor type |
| Specifications | General computing s6, 2 vCPUs, 4 GiB | The size of each new server |
| Image | Private image, image-web | The copy of ecs-web to start from |
| Disk | System disk, High I/O, 40 GiB | The disk for each new server |
| Security group | sg-web | The firewall rules for new servers |
| EIP | Do not use | New servers get no public IP; the load balancer handles public access |
| Login mode | Password | How you log in to new servers |
| Password | Set the lab password, or your own | The login password for new servers |

Click **Create Now**.

**Why no EIP:** The load balancer is the only public entrance. Each server would otherwise need its own public address, which costs money and gives attackers more targets.

---

#### Step 3: Create an AS group

**What you do:** Go back to **AS Configuration List**, click **Create AS Group**, and set:

| Setting | Value | What it means |
|---|---|---|
| Region | AP-Singapore | Same region |
| AZ | Default | Use the default placement |
| Multi-AZ scaling policy | Balanced | Spread servers evenly across AZs |
| Name | as-group-web | The name of the group |
| Max. instances | 5 | The group never grows past 5 servers |
| Expected instances | 2 | The group starts with 2 servers |
| Min. instances | 1 | The group never shrinks below 1 server |
| AS configuration | as-config-web | The template from Step 2 |
| VPC / Subnet | vpc-primary / subnet-web | Where the new servers are placed |
| Load balancing | elb-web, server_group-web, port 80, weight 1 | Connects the group to the load balancer |
| Instance removal policy | Oldest instance created from oldest AS configuration | Decides which server is removed first during scale-in |

Click **Create Now**, then wait a few minutes. The instance count should reach 2.

**What the three numbers mean:**
- **Min 1** is the lowest the group can drop to.
- **Expected 2** is the number the group tries to keep.
- **Max 5** is the highest the group can grow to.

**Why link the load balancer:** New servers are added to `server_group-web` automatically, so they start receiving traffic without any manual change.

---

#### Step 4: Create the scale-out policy (CPU high)

**What you do:** Open the AS group `as-group-web` and click **View AS Policy**, then **Add AS Policy**. Set:
- Policy name: `as-policy-web`
- Policy type: **Alarm**
- Alarm rule: **Create**, named `as-alarm-web`
- Monitoring type: **System monitoring**
- Trigger condition: **CPU usage, Max., >, 70, %**
- Monitoring interval: **5 minutes**
- Consecutive occurrences: **2**
- Alarm policy type: **Simplified scaling**
- Scaling action: **Add 1 instance**
- Cooldown period: **300 seconds**

Click **OK**.

**What this means in plain words:** Every 5 minutes, check the highest CPU value. If it is above 70% in two checks in a row, add one server.

**Example:** At 20:00, the checkout servers hit 75% CPU in two checks. The group adds one server, and the load balancer starts sending it requests.

**Why two checks:** A single spike, such as a short burst, should not add a server. Two checks in a row show a real trend.

**Why the cooldown:** After adding a server, the group waits 300 seconds before it starts another scaling action. This gives the new server time to start and take its share of traffic.

---

#### Step 5: Create the scale-in policy (CPU low)

**What you do:** Click **Add AS Policy** again. Create a policy that removes one instance when CPU usage is **below 30%** for **two consecutive** checks. Use the same pattern as Step 4, with the action set to **remove 1 instance**.

**What this means:** When the load drops, the group removes an extra server to save money.

**Example:** After the sale, CPU drops to 10%. The group removes one server.

---

#### Step 6: Check the policies and run one manually

**What you do:** Open the AS policy list. Both policies should show **Enabled**. To test one right away, click **Execute Now** on the policy.

**What this shows:** Executing a policy runs its action immediately, without waiting for the alarm. It is a quick way to check that scaling works.

---

#### Step 7: Verify the service through the load balancer

**What you do:** In the Elastic Load Balance console, copy the EIP of `elb-web`. Open a browser and go to `http://EIP:80`.

**What you should see:** The forum still loads, even though the group now has more servers.

---

#### Step 8: Test automatic scale-out with a CPU stress test

**Part A: Get the public address of a new server**

**What you do:** In the ECS console, select a server that Auto Scaling created, choose **More > Manage Network > Bind EIP**, and bind a new EIP. Use these settings:
- Billing: **Pay-per-use**
- Region: **AP-Singapore**
- EIP type: **Dynamic BGP**
- Billed by: **Traffic**
- Bandwidth: **5 Mbit/s**

Click **Next**, confirm, and **Submit**. Then go back to the ECS console, refresh the EIP list, and bind the new EIP.

**Why:** You need a remote login path to the server to run the stress test.

**Part B: Log in and install the stress tool**

**What you do:** Click **Remote Login** on the right of the server and log in with **VNC** or **CloudShell**. Run as `root`:

```
yum -y install stress
```

**Part C: Start the load**

```
stress --cpu 2 --timeout 900
```

**Part D: Watch the result**

**What you do:** Go to the AS group's **Monitoring** tab. The CPU usage of the group's instances rises.

**Timing:** The scale-out policy needs two checks in a row, each 5 minutes apart. Wait at least 10 minutes before you expect a new server. Keep the stress test running during that time.

**Important:** The stress test needs at least one instance in the group while it runs. If the group has no instances, the test fails.

---

### Section 4: Auto Scaling for bandwidth scaling

**Overview:** This section scales the network bandwidth of the load balancer's public address. When incoming traffic rises, the bandwidth grows automatically.

---

#### Step 1: Create the bandwidth scaling policy

**What you do:** In the Auto Scaling console, choose **Bandwidth Scaling** from the navigation pane and click **Create Bandwidth Scaling Policy**. Set:
- Region: **AP-Singapore**
- Policy name: `as-policy-web`
- Resource type: **EIP**
- EIP: the EIP bound to **elb-web**
- Policy type: **Alarm**
- Alarm rule: **Create**, named `as-alarm-web`
- Trigger condition: **Inbound bandwidth, Max., >, 18, bit/s** (see the note in Section 9)
- Monitoring interval: **5 minutes**
- Consecutive occurrences: **3**
- Alarm policy type: **Simplified scaling**
- Scaling action: **Set to 30 Mbit/s**
- Cooldown period: **300 seconds**

Click **Create Now**. The page should show the policy as enabled.

**What this means:** Every 5 minutes, check the highest inbound traffic. If it is above the limit three checks in a row, set the bandwidth to 30 Mbit/s.

**Why three checks:** Three checks in a row (about 15 minutes) show a sustained traffic rise, not a short burst.

**Example:** Traffic to the forum grows from a few megabits to over the limit during a promotion. The bandwidth grows to 30 Mbit/s, so the forum stays fast.

---

### Section 5: Maintaining Auto Scaling resources

**Overview:** Auto Scaling works on its own, but you still need to manage it. This section covers manual control, protection and notifications.

---

#### Step 1: Add an instance manually during a traffic spike

**What you do:** Open the AS group `as-group-web`, go to the **Instances** tab, click **Add**, select `ecs-web`, and click **OK**.

**Why:** When traffic rises suddenly, you may not want to wait for an alarm. Adding a server by hand gives immediate extra capacity.

---

#### Step 2: Enable instance protection

**What you do:** On the **Instances** tab, find `ecs-web` and turn on **Instance Protection**.

**What this does:** It stops Auto Scaling from removing this server during scale-in.

**What it does not do:** If the server fails a health check, Auto Scaling still removes it. Protection does not keep a broken server.

**Optional check:** Open **Scaling Actions** and wait about 5 minutes. A scale-in policy should trigger, and one instance other than `ecs-web` should be removed.

**Example:** ShopFast keeps its main checkout server protected, so the group only removes the newer servers.

---

#### Step 3: Change the specification of the instances

**What you do:** Open the AS group, choose **More > Modify AS Configuration**, and in the **Specifications** area deselect `s6.large.2` and select **General computing-plus c7 c7n.large.4**.

**What this does:** New servers the group creates will use the new specification. Existing servers keep their old size unless you replace them.

**Why:** A workload may need more CPU or memory over time. This lets you change the server size without building a new group.

---

#### Step 4: Configure notifications

**What you do:**
1. Open the AS group and go to the **Notifications** tab, then click **Add Notification**.
2. Select all notification events and click **Create Topic**.
3. Enter the topic details and click **OK**.
4. Return to **Add Notification**, select the new topic, and click **OK**.

**What this does:** A message is sent whenever a scale-out or scale-in action succeeds or fails.

**Why:** You want to know when the group changes, even when you are not watching the console.

**Note:** As in the O&M lab, the email address in the topic must be confirmed from the confirmation email before messages arrive.

---

## 5. Commands in this lab, explained

The lab uses two commands in the CPU stress test. Both run on the new server, over the remote login.

### `yum -y install stress`

- `yum`: the package manager on Red Hat–style Linux. It downloads and installs software.
- `-y`: answer "yes" to every question automatically, so the install does not stop and wait.
- `install stress`: install the program named `stress`.

**Example:** This is like ordering a tool from a catalogue. `yum` is the shop, `install` is the order, and `stress` is the tool.

**Why root:** Installing software changes the whole system, so it needs administrator rights.

### `stress --cpu 2 --timeout 900`

- `stress`: a test program that puts artificial load on the computer.
- `--cpu 2`: start 2 worker processes. Each one keeps the CPU busy with square-root calculations.
- `--timeout 900`: stop automatically after 900 seconds (15 minutes).

**Example:** It is like having two cashiers work nonstop for 15 minutes. The server's CPU usage climbs, and the AS policy sees it.

**To stop early:** Press `Ctrl+C` in the same window. The test ends right away.

---

## 6. The full chain (draw this)

```
Users → elb-web (one public address)
        → server_group-web
        → ecs-web and the servers Auto Scaling adds
        → rds-web (database in subnet-db)

High CPU on the servers
  → Cloud Eye sees the value over 5-minute checks
  → alarm fires after 2 checks above 70%
  → as-policy-web adds 1 server
  → new server joins server_group-web
  → load balancer starts sending it traffic

High inbound traffic
  → bandwidth alarm fires after 3 checks
  → EIP of elb-web set to 30 Mbit/s
```

**Task:** Draw this on paper. Next to each arrow, write the section of the lab that sets it up.

---

## 7. Common mistakes

| Problem | Likely cause | Fix |
|---|---|---|
| Forum does not load through the load balancer | Backend port is not 80, or listener is not TCP 80 | Check the listener and backend port |
| Installer cannot connect to the database | Wrong database IP, wrong password, or `sg-db` source wrong | Use the private IP of rds-web and the `ecs-web` private IP as the source |
| New servers have no forum | Image was made from a wrong server, or created too early | Create `image-web` from `ecs-web` after Discuz! is installed |
| AS group stays at 1 or 2 servers | Trigger not met yet, or cooldown still running | Wait for 2 checks; check the policy status |
| Stress test ends early or fails | No instance in the group while the test runs | Keep at least one instance running |
| Bandwidth does not change | Wrong EIP selected in the bandwidth policy | Select the EIP bound to elb-web |
| New server has no public IP but you need to log in | EIP was not bound | Bind a new EIP (Section 3, Step 8, Part A) |
| Unexpected charges | Resources left running after the lab | Release the EIPs, load balancer, and extra servers when you finish |

---

## 8. Review questions and answers

1. **Why does the load balancer get the EIP, and not ecs-web?** The load balancer is the single public entrance. Servers behind it do not need their own public address, which keeps them hidden from direct internet access.
2. **Why is `Do not use` selected for EIP in the AS configuration?** The new servers are reached through the load balancer, so they do not need their own public IP.
3. **What does the minimum, expected and maximum number of instances control?** The lowest, the target, and the highest number of servers in the AS group.
4. **Why does the CPU policy need 2 consecutive checks?** To avoid adding a server because of a short spike. Two checks in a row show a real trend.
5. **Why is there a cooldown period?** It stops another scaling action from starting while the last one is still taking effect.
6. **What does instance protection do, and what does it not do?** It stops Auto Scaling from removing the protected server during scale-in. It does not stop removal if the server fails a health check.
7. **What does `stress --cpu 2 --timeout 900` do?** It starts 2 processes that keep the CPU busy, and stops them after 900 seconds.
8. **Why is `yum` run as root?** Installing software changes the whole system, so it needs administrator rights.
9. **Why is the database placed in a private subnet with a security group that allows only ecs-web?** So customers and attackers cannot reach it directly, and only the web server can connect.

---

## 9. Points to know before you start

**1. Passwords in the lab text.** The lab text uses one example password in several places. Use the lab's password or set your own, and write it down. Lost database passwords cannot be recovered.

**2. Region must match.** Every resource must be in AP-Singapore. Resources in different regions cannot be connected, so the load balancer cannot reach servers in another region.

**3. Unbinding the EIP changes how you reach ecs-web.** After Section 2, Step 1, you can no longer open the forum through ecs-web's own public address. Use the EIP of elb-web instead.

**4. Waiting time for scaling.** The CPU policy checks every 5 minutes and needs 2 checks, so you wait at least 10 minutes. The bandwidth policy needs 3 checks, so you wait about 15 minutes. Do not repeat the test during the wait, as this makes the results harder to read.

**5. The bandwidth trigger unit.** The lab text lists the trigger as **18 bit/s**, while the scaling action is **30 Mbit/s**. 18 bit/s is an extremely small value, so the number or unit is probably a typo. Check the value and unit on the console page before you save the policy, and choose a limit that real test traffic can cross.

**6. The scale-in policy is brief in the lab text.** Only the scale-out policy is fully listed. For the scale-in policy, use the same fields in the opposite direction: CPU below 30%, two consecutive checks, remove one instance.

**7. Cost.** Pay-per-use load balancers, EIPs, extra servers and traffic are all billed while they run. The stress test and the extra EIP on a new server cost money while active. Release the resources you no longer need.

**8. Resources are released.** The lab says resources are released when the time runs out or when you exit. Save your screenshots and notes before the time is up.