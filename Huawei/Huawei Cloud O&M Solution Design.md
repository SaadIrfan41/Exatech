# Huawei Cloud O&M Solution Design: Student Handout

## Course Objectives

After this class you will be able to:

1. Explain Huawei Cloud's multi-layer O&M (operations and maintenance) approach.
2. Describe what Cloud Eye, APM (Application Performance Management), AOM (Application Operations Management), and LTS (Log Tank Service) do, and when to use each.
3. Explain how alarms and notifications flow from monitoring data to a person or an automated action.
4. Explain how RFS (Resource Formation Service) automates building and changing cloud resources.
5. Suggest simple ways to improve a service architecture so it is easier to operate.

---

## Part 1: What Is O&M and Why Do We Need It?

**O&M** means keeping a running system healthy: watching it, finding problems, fixing them, and making routine changes safely.

Think about an online shop called **ShopFast**. On a normal day, orders come in steadily. On a sale day, traffic jumps ten times. Someone must answer these questions:

- Is the server busy or overloaded?
- Is the checkout page throwing errors?
- Which log line explains why a payment failed?
- Can we add servers automatically when traffic spikes?

O&M tools answer these questions. Huawei Cloud groups them by layer.

### The Four Questions Behind Each Layer

| Question a team asks | Huawei Cloud service | Layer |
|---|---|---|
| Is the business working? | Cloud Eye, custom metrics | Business layer |
| Is the infrastructure healthy? (CPU, memory, disk, network) | Cloud Eye, AOM | Infrastructure |
| Where are the errors in the code and logs? | LTS, AOM | Logs and processes |
| Which API or service call is slow? | APM | Application |

> **Key idea:** Monitoring tells you *something is wrong*. Logs and tracing tell you *where* and *why*. Alarms tell the right people, or a system, to act.

### The Three Layers of the O&M Model

Huawei describes modern systems as three layers. Each layer needs its own monitoring.

| Layer | Examples | What can go wrong |
|---|---|---|
| Application layer | Microservices, processes, application performance | Slow API, exception in code |
| Platform software layer | Databases, middleware, containers, operating systems | Database full, container crash |
| Infrastructure layer | Clusters, virtual machines (VMs), networks, disks | Disk full, network latency |

**Pain point:** In a distributed system (many services working together, often scaling up and down), a request may pass through ten services. When something fails, it is hard to know which one caused it. The data is also scattered across many tools.

**Huawei's answer:** Combine AOM, LTS, and APM so that metrics, logs, and application traces can be viewed together.

---

## Part 2: The O&M Map (Which Tool for Which Question?)

Think of the layers as a pyramid. Each tool sits at a level and answers one kind of question.

| Level | Tool | Main question it answers |
|---|---|---|
| Top | APM | How is my application performing at each call? |
| Second | LTS | What do the logs say? |
| Third | AOM | How are my applications and processes doing, and what alarms are open? |
| Base | AOM, Cloud Eye, CTS | How are the cloud resources (infrastructure) doing? |

Two things to note:

- **CTS is not a monitoring tool.** CTS (Cloud Trace Service) records *who did what* on your cloud account, such as who created or deleted a server. It supports auditing and compliance. It is not used to watch CPU.
- **AOM is the umbrella platform.** It brings together data from Cloud Eye, LTS, APM, and other sources in one place.

### Mini Example: ShopFast Checkout Is Slow

1. **Cloud Eye** shows the checkout server's CPU jumped to 95%.
2. **APM** shows the slow part is a call to the payment API, which takes 4 seconds.
3. **LTS** shows the error message: "database connection timeout."
4. **AOM** groups these together and shows the open alarm.

No single tool answered everything. Together, they helped the team find the problem.

---

## Part 3: Cloud Eye (Resource Monitoring)

### What Cloud Eye Does

Cloud Eye is a **multi-dimensional resource monitoring service**. You use it to:

- Monitor cloud resources (such as servers and disks) and their **metrics** (numbers that describe state, such as CPU usage).
- Set **alarm rules** (for example, "tell me when CPU is above 80% for 5 minutes").
- Find problems quickly and respond to changes.

### Four Main Features

| Feature | What it means |
|---|---|
| Automatic provisioning | Cloud Eye is ready for every user. You do not install it to start getting basic metrics. |
| Real-time monitoring | Raw data is reported to Cloud Eye. When a value crosses a threshold, an alarm is triggered and notifications are sent. |
| Multiple notification types | Notifications go by email, SMS, or HTTP/HTTPS request (a message sent to another system). |
| Visualized monitoring | Dashboards and graphs compare several metrics and refresh automatically. |

### How Data Flows

```
Data collection → Data processing → Data storage → Alarm notification
                                              ↘ Data display (dashboards)
```

Plain English:

1. Cloud Eye **collects** metric values from resources.
2. It **processes** them, for example by calculating averages.
3. It **stores** them for a period of time.
4. It **sends an alarm** if a rule is broken, and it **shows** the data on dashboards.

### Important Concept 1: Agent-Free Versus Agent-Based Monitoring

Some metrics need no extra software. Others need the **Cloud Eye agent**, a small program installed on the server.

| Monitoring type | Where it applies | What you get |
|---|---|---|
| Basic monitoring (no agent) | Cloud services such as ECS, BMS, EVS (disks), VPC (networks) | Basic metrics reported by the service itself |
| Agent-based (OS monitoring) | Servers (ECS and BMS) where the agent is installed | More detailed OS metrics such as memory, disk usage, and process information |

**Remember:** The agent is installed on servers. You do not install it on a disk or a network. Disk and network metrics are reported by the service itself.

**Example:** ShopFast installs the agent on its web servers so it can see memory use. Its disk volumes (EVS) and its virtual network (VPC) report their own metrics without the agent.

### Important Concept 2: How Long Is the Data Kept?

Cloud Eye keeps data at different levels of detail.

**Raw data** is the value as it was reported. **Rolled-up data** (also called aggregated data) summarizes raw values over a period, such as the average over 5 minutes.

| Data kind | How long it is kept |
|---|---|
| Raw data | 2 days |
| 5-minute rollup | 10 days |
| 20-minute rollup | 20 days |
| 1-hour rollup | 155 days |
| 4-hour rollup | 300 days |
| 1-day rollup | 5 years |

**Why this matters:** Short-term problems are best seen in raw data. Long-term trends (for example, "is our traffic growing each year?") use daily rollups. If you need to keep data longer than the retention period, you can export it, for example to OBS (Object Storage Service).

**How often data is collected:** Basic ECS metrics are reported every 5 minutes. Agent-based OS metrics are collected every minute.

### Important Concept 3: Aggregation

**Aggregation** means combining many raw values into one summary value for a time period. Cloud Eye can summarize with the average, maximum, minimum, sum, or variance.

**Example:** ShopFast's CPU is reported every minute. Over a 5-minute period, Cloud Eye records the **average** CPU and the **maximum** CPU. A short spike is visible in the maximum even if the average looks normal.

---

## Part 4: LTS (Log Tank Service)

### What Is a Log?

A **log** is a text record that a system writes about what it is doing. Examples:

```
2026-11-13 19:20:01  INFO   order 4471 created
2026-11-13 19:20:03  ERROR  payment gateway timeout, order 4471
```

Logs are the "diary" of your servers, applications, and cloud services. The problem is that a busy system writes millions of lines. Reading them on each server one by one is not practical.

### What LTS Does

LTS **collects** logs from hosts and cloud services, then **analyses** them in real time. It helps you:

- **Search logs** by keyword or SQL query.
- **Visualize** information as charts.
- **Set alarms** on log patterns, such as "more than 50 ERROR lines in 5 minutes."
- **Get statistics** from logs quickly.
- **Connect to big data** tools for deeper analysis.

### Where Logs Come From

| Source | Example |
|---|---|
| ELB logs | Records of requests passing through the load balancer |
| ECS logs | Application and system logs from virtual servers |
| Container logs | Output from containers in a container platform |
| Open-source logs | Logs from software you run yourself |

### LTS Features in Simple Terms

| Feature | Plain-English meaning |
|---|---|
| Log search | Find lines that match a word or a SQL-style question |
| Real-time analysis | See logs as they arrive, not hours later |
| Log cleaning | Tidy messy logs into a standard format |
| Intelligent clustering | Group similar log lines together automatically, so 10,000 similar errors appear as one group |
| Alarms | Trigger a notification when a log pattern appears |
| Report display | Show results as charts |

You do not need to memorize every feature. Focus on the four main ones: **collect, search, alarm, and visualize.**

### Why Use LTS Instead of Logging In to Each Server?

1. **Central place:** All logs appear in one place, even from many servers.
2. **No need to log in:** Developers see logs without connecting to a faulty server.
3. **Faster fixes:** Errors appear in charts and alarms as they happen.

### LTS Versus CTS (Common Confusion)

| | LTS | CTS |
|---|---|---|
| Records | What the *applications and servers* print | What *users* did on the cloud account |
| Typical use | Troubleshooting and performance analysis | Security audit and compliance |
| Example question | "Why did checkout return an error at 19:20?" | "Who deleted the test database last Tuesday?" |

---

## Part 5: APM (Application Performance Management)

### What APM Does

APM helps **locate slow code and failing service calls** in an application. While Cloud Eye tells you that a server is busy, APM tells you **which call inside the application** is slow.

APM uses **agents** (software added to the application). These agents record **traces**, which are the complete path of one request through many services.

### Key Terms

| Term | Meaning |
|---|---|
| Trace | The full journey of one request, from the first service to the last |
| Span | One step inside a trace, such as one database query |
| Topology | A map of which services call which other services |
| Apdex | A score from 0 to 1 that shows how satisfied users are with response time |
| Transaction | A business action, such as "place order," measured from start to end |

**Apdex colors:** The score is shown in colors. Green means good (0.75 to 1). Other colors show slower responses.

### APM Functions

- **Application metric monitoring:** Measures the health of the application, such as request counts and response times.
- **Tracing:** Shows each step of a request.
- **Application topology:** A visual map of service calls.
- **Intelligent alarm reporting:** Sends alarms when application behaviour changes.

### Example: ShopFast Checkout With APM

A customer clicks "Pay." APM shows:

```
Checkout (120 ms)
 ├─ Cart service (15 ms)
 ├─ Payment service (3,900 ms)   ← slow step
 │    └─ Database query (3,850 ms)  ← root cause
 └─ Email service (40 ms)
```

Without APM, the team would only see "checkout is slow." With APM, they know the slow part is a database query inside the payment service.

### Which Languages Does APM Support?

APM supports applications written in Java, Python, Node.js, Go, PHP, C++, and .NET.

---

## Part 6: AOM (Application Operations Management)

### What AOM Does

AOM is a **one-stop, multi-dimensional O&M platform** for cloud applications. It brings together data from several sources:

- Cloud Eye (metrics)
- LTS (logs)
- APM (application performance)
- Other sources, such as Prometheus (an open-source metrics system)

In one place, you can see dashboards, alarms, and resource status.

### AOM Main Areas

| Area | What you do there |
|---|---|
| Access center | Connect data sources (metrics, logs, and traces) |
| Dashboards | Put key charts for an application on one screen |
| Alarm center | Manage alarms and events, and choose how to be notified |
| Infrastructure monitoring | Check hosts, containers, and cloud services |
| Log management | Search and analyze logs (AOM uses LTS for log functions) |
| Automation | Run scripts and routine tasks in batches |

### Alarm Notifications

AOM can notify you by email, SMS, voice, and chat or webhook tools. You can use **message templates** so that every alarm message contains the same useful details.

### Example: ShopFast With AOM

ShopFast's operations team opens one AOM dashboard for the checkout application. It shows:

- CPU and memory of the web servers (from Cloud Eye)
- Error count per minute (from LTS)
- Slowest payment calls (from APM)
- Open alarms (from AOM's alarm center)

Everything is in one screen, so the on-call engineer does not need to switch between four tools.

---

## Part 7: Putting It Together (The End-to-End Workflow)

Here is how the tools work together for a real incident.

| Step | What happens | Tool |
|---|---|---|
| 1 | The application writes logs and reports custom metrics | Application |
| 2 | Logs are collected and searched | LTS |
| 3 | Built-in cloud metrics arrive from ECS and other resources | Cloud Eye |
| 4 | A log pattern or metric crosses a threshold, so an alarm is raised | LTS or Cloud Eye |
| 5 | The alarm is sent to a notification topic | SMN (Simple Message Notification) |
| 6 | The topic sends an email, an SMS, or runs a function | SMN, FunctionGraph |
| 7 | Dashboards show the trend for the team to review | LTS dashboards, Cloud Eye dashboards |

**Walk-through with ShopFast:**

1. Payment errors appear in the application logs.
2. LTS counts the errors and an alarm rule fires.
3. The alarm goes to SMN.
4. SMN sends an email to the on-call engineer and runs a FunctionGraph function that posts a message to the team chat.
5. The engineer opens the dashboard, finds the failing payment call in APM, and fixes it.

**Note on "Functions":** In the slide, "Functions" means FunctionGraph, a service that runs small pieces of code when triggered.

---

## Part 8: Automating O&M With RFS

### Why Automate?

Building resources by hand (clicking in the console) is slow and easy to get wrong. If you need the same setup in three regions, you must repeat every click exactly. Automation solves this.

### What RFS Does

**RFS (Resource Formation Service)** creates cloud resources in **batches** from a **template**. It helps you create, manage, and upgrade resources in a way that is efficient, secure, and consistent.

### Key Terms

| Term | Plain-English meaning |
|---|---|
| Template | A text file that describes the resources you want (for example, two servers and a network) |
| Stack | A group of resources that RFS creates, updates, or deletes together as one unit |
| HCL | The HashiCorp Configuration Language, the text format used in templates |
| Infrastructure as Code (IaC) | Describing infrastructure in files instead of clicking, so it can be repeated and reviewed |

### Template Formats

RFS templates can be **.tf**, **.tf.json**, or **.zip** files that use HCL syntax. RFS works with Terraform, a common IaC tool.

### The RFS Cycle

```
1. Write the template (describe the target state)
        ↓
2. Upload it to RFS and create a stack
        ↓
3. RFS builds the resources in Huawei Cloud
        ↓
4. Change the template when needs change, then update the stack
```

### Why Templates Help ShopFast

- **Repeatable:** The same template builds the test and production environments.
- **Quick recovery:** If a region fails, the same template rebuilds the setup elsewhere.
- **Reviewed changes:** Changes are made in a file that the team can check before applying.

---

## Part 9: Improving Your Service Architecture

Good monitoring is easier when the architecture is simple to observe. The principles below are general practice. Confirm any Huawei-specific feature before using it in a project.

| Principle | Example for ShopFast |
|---|---|
| Put a load balancer in front of servers | Traffic is spread across several web servers, so one busy server does not stop the shop |
| Scale out when traffic rises | Auto scaling adds web servers during a sale and removes them afterwards |
| Monitor every layer | Watch the infrastructure, the database, and the application separately |
| Keep logs in one place | Send all server logs to LTS, not to each server's disk |
| Alarm on user impact | Alarm on "checkout errors per minute," not only on CPU |

**Tip:** The best alarm is one that tells you what users feel. CPU at 90% is only a warning. Failed payments are an emergency.

---

## Part 10: Glossary

| Term | Meaning |
|---|---|
| Agent | A small program installed on a server to collect extra data |
| AOM | Application Operations Management, a one-stop O&M platform |
| APM | Application Performance Management, which finds slow application calls |
| Aggregation | Combining many raw values into one summary for a period |
| Alarm rule | A condition, such as "CPU above 80% for 5 minutes," that triggers an alarm |
| Cloud Eye | Huawei Cloud's resource monitoring service |
| CTS | Cloud Trace Service, which records who did what on the account |
| Dashboard | A screen that shows key charts together |
| Log | A text record written by a system about its activity |
| LTS | Log Tank Service, which collects and analyzes logs |
| Metric | A number that describes state over time, such as CPU usage |
| Rollup | Another word for aggregated data over a time period |
| RFS | Resource Formation Service, which builds resources from templates |
| SMN | Simple Message Notification, which sends alarms by email, SMS, or other channels |
| Trace | The full path of one request through many services |

---

## Part 11: Review Questions

1. What is the difference between a metric and a log?
2. Why does Cloud Eye need an agent on an ECS but not on an EVS disk?
3. A ShopFast manager asks, "How long can we look at last year's CPU data?" Which rollup level answers this, and what is its retention?
4. Which service would you use to find that a slow checkout is caused by a database query inside the payment service?
5. A team member says, "CTS shows our CPU use." Is this correct? Explain.
6. Why is RFS useful when you need to build the same environment in two regions?
7. Name two ways an architecture can be changed so it is easier to monitor and operate.

---

## Instructor Answer Key

Use this section for marking. Do not give it to students before the review.

1. **Metric versus log:** A metric is a number measured over time (for example, CPU at 60%). A log is a text record of an event (for example, "payment failed for order 4471"). Metrics show *that* something changed. Logs show *what* happened.

2. **Agent on ECS, not EVS:** The agent runs software inside the operating system of a server, so it is needed to read OS-level metrics. An EVS disk is a storage volume, and its basic metrics are reported by the storage service itself. A disk has no operating system to run an agent.

3. **Last year's CPU data:** Use the 1-day rollup. It is kept for 5 years. Raw data (2 days) and 5-minute rollups (10 days) would not cover last year. The 1-hour rollup (155 days) would also not cover it.

4. **Finding the database query:** APM. It records traces and shows the spans inside each request. Cloud Eye would show the server is busy. LTS would show log errors but not the call path.

5. **"CTS shows our CPU use":** Incorrect. CTS records operations on the cloud account, such as who created or deleted a resource. CPU usage is a metric, shown in Cloud Eye.

6. **RFS for two regions:** The same template creates the same resources in both regions, so the environments match. Changes are made once in the template and applied again, which reduces manual mistakes.

7. **Architecture changes (any two):** Add a load balancer in front of servers. Use auto scaling so capacity follows demand. Send all logs to one central place. Create alarms based on user impact, such as failed payments, instead of only on infrastructure metrics.

---

## Source Notes for the Instructor

Before class, check these items against the current Huawei Cloud documentation:

- **Cloud Eye retention:** The rollup periods and retention times in Part 3 come from the Cloud Eye FAQ. The slide said "five years" and "last six months." Use the table in this handout instead.
- **Agent scope:** Basic monitoring is agent-free for ECS and BMS. Some ECS memory and disk metrics need the agent or UVP VMTools. Confirm the list for the course image.
- **AOM feature names:** Huawei has renamed or retired some AOM features (for example, Application Insights, which is being moved to COC). Check the console before teaching the menu names.
- **APM agents:** Confirm the supported languages and agent behavior for the lab environment.
- **Architecture principles (Part 9):** These are general good practice, not a Huawei-specific claim. Do not present them as product features unless verified.
- **Slide excerpt:** The source deck skips many slide numbers. This handout covers the full O&M topic so students do not need the missing slides.