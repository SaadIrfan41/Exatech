# Huawei Cloud Storage Solution Design

**Level:** Beginner
**Prerequisite:** Compute Solution Design (ECS, EVS, SFS basics)
**What you will do:** Learn how Huawei Cloud stores data, choose the right storage for each job, and check your understanding with short questions.

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. Explain the difference between block, file, and object storage.
2. Describe what a bucket, an object, and a key are in OBS.
3. Choose an OBS storage class based on how often data is accessed.
4. Use lifecycle rules and versioning to control cost and protect data.
5. Explain how OBS keeps data private and how to share a file temporarily.
6. Choose between EVS, SFS, and OBS for a given workload.

---

## Running Example: The ShopFast Online Store

We continue with ShopFast, the online store from the compute lecture. This time we focus on where its data lives.

| Data | Example | Which storage? |
|---|---|---|
| Operating system and database | Server disk, order database | EVS (block) |
| Customer uploads being processed by several servers | Return-form photos before review | SFS (file) |
| Product photos and invoices | Images on the website, yearly tax invoices | OBS (object) |

---

## Part 1: Three Types of Storage

Huawei Cloud storage comes in three main types. Each one is accessed in a different way.

| Type | Service | How the server sees it | Example |
|---|---|---|---|
| **Block** | EVS | A disk, which you format and mount | The disk that holds the operating system |
| **File** | SFS | A shared folder that many servers can open | A folder of uploads used by several web servers |
| **Object** | OBS | A collection of files reached through a web address | Product photos loaded by a browser |

**Key idea:** Block storage acts like a disk. File storage acts like a shared folder. Object storage is accessed through web requests, and the server never sees a disk at all.

---

## Part 2: What Is OBS?

**Object Storage Service (OBS)** stores unstructured data, such as images, videos, documents, backups, and logs. You access it over HTTP or HTTPS, using the console, SDKs, REST APIs, or command-line tools.

### 2.1 The building blocks

Three words describe how OBS organizes data:

```
OBS service
   │
   └── Bucket: shopfast-media          (a container with its own rules)
          ├── Object: products/42/main.jpg
          ├── Object: products/42/thumb.jpg
          └── Object: invoices/2026/inv-1001.pdf
```

| Term | Meaning | Simple comparison |
|---|---|---|
| **Bucket** | A container that groups objects and holds shared settings | A labeled filing cabinet |
| **Object** | One stored item, which includes its data and information about it | One file in the cabinet |
| **Key** | The unique name of an object inside its bucket | The label on the file |
| **Metadata** | Key-value details about the object, such as content type | A note attached to the file |
| **Data** | The actual content, such as the image bytes | The file's contents |

**Important rule:** Within one bucket, every key must be unique. Two objects can have the same metadata, though. For example, two photos can both be marked `Content-Type: image/jpeg`.

### 2.2 Key limits

- **Unlimited capacity:** A bucket can hold any number of objects.
- **Maximum object size:** Up to 48 TB per object.
- **Durability:** 12 nines (99.9999999999%).
- **Availability:** 99.995%.

**What "12 nines" means:** Durability is the chance that stored data is not lost. Twelve nines means the expected loss is extremely small. As a rough illustration, if you stored 10 billion objects, you would expect to lose about one object every 100 years. This is an illustration of the number, not a guarantee.

> **Note:** Confirm current limits and durability figures in the official OBS documentation before quoting them.

### 2.3 How OBS stays reliable

OBS protects data at several levels, so one failure does not lose it:

1. **Storage media:** Failing or slow disk sectors are detected and isolated.
2. **Servers:** Data is split into fragments and spread across servers using erasure coding, so a server failure does not lose data.
3. **Cabinets:** Power and network are redundant across racks.
4. **Data centers:** Data is spread across Availability Zones, so a local fire or power failure does not lose data.
5. **Regions:** Data can be replicated to another region to survive a large regional disaster.

---

## Part 3: OBS Storage Classes

Not all data is used the same way. OBS offers three classes, and you pay for the class that matches how often you read the data.

| Class | Use it for | Retrieval | Cost pattern |
|---|---|---|---|
| **Standard** | Data read often, such as website images | Immediate | Higher storage cost, low request cost |
| **Infrequent Access** | Data read occasionally, such as old backups | Immediate | Lower storage cost, higher cost per read |
| **Archive** | Data kept for years and rarely read, such as compliance records | Requires restore, which takes time | Lowest storage cost |

**ShopFast example:**
- Product photos shown on the homepage: **Standard**
- Last year's order backups, kept for quick recovery: **Infrequent Access**
- Tax invoices kept for seven years for the accountant: **Archive**

**Quick check:** A backup is needed only if something goes wrong, which is almost never. Which class fits best, and what is the trade-off?

---

## Part 4: Lifecycle Rules and Versioning

### 4.1 Lifecycle rules

A **lifecycle rule** moves or deletes objects automatically based on their age. You set it once, and OBS applies it.

```
Invoice created
   │
   ▼  after 30 days
Infrequent Access
   │
   ▼  after 365 days
Archive
   │
   ▼  after 7 years
Deleted
```

Lifecycle rules keep costs down because older data moves to cheaper classes without anyone doing it by hand. The day numbers above are examples. Choose values that match your business rules.

### 4.2 Versioning

With **versioning** turned on, every upload of the same key gets a unique **version ID**. If someone overwrites or deletes a file by mistake, the earlier version is still there.

When you delete an object in a versioned bucket, OBS adds a **delete marker** instead of erasing the data. Removing the marker brings the object back.

**ShopFast example:** An editor replaces the homepage banner with the wrong image. Versioning lets the team restore the previous banner in a few clicks.

Lifecycle rules can also delete old versions automatically, so storage does not grow forever.

---

## Part 5: Keeping Data Private

By default, every OBS bucket and object is **private**. Only the owner can access it. You can open access in controlled ways:

| Method | What it does | Example |
|---|---|---|
| **Bucket policy** | JSON rules that allow or deny actions for specific users | Allow the web app's role to read product images |
| **ACL** | Basic account-level read or write access | Give a partner read access to one bucket |
| **IAM permissions** | Fine-grained control over who can do what | Accountants can read invoices, but not delete them |
| **Signed URL** | A temporary link that expires after a set time | A customer downloads one invoice for 10 minutes |

**Signed URL example:** A customer asks for a copy of an invoice. ShopFast generates a link that works for 10 minutes. After that, the link stops working, and the bucket stays private.

**Encryption:** Data can be encrypted on the server (stored encrypted) or on the client (encrypted before upload). Data moving over the network uses HTTPS.

---

## Part 6: Hosting a Static Website

OBS can host a static website, which means pages made only of HTML, CSS, JavaScript, and images. There is no server-side code.

To use a custom domain:
1. Create a bucket and upload the website files.
2. Make the objects you want visitors to see publicly readable.
3. Point your domain to the bucket address with a **CNAME** record.

For example, `www.shopfast.example` can point to a bucket address such as `shopfast-site.obs.<region>.myhuaweicloud.com`. Replace `<region>` with the region you use.

> **Note:** Static hosting is for static pages only. Anything that needs server-side logic, such as checkout, belongs on ECS or a serverless service.

---

## Part 7: Object Naming

Object keys are the names used to find files, so they affect performance.

- **Use clear, consistent names** such as `products/42/main.jpg`. This makes folders easy to browse in the console.
- **Be careful with keys that all start the same way.** Keys that begin with the same sequence, such as a timestamp, can concentrate requests on one part of the system.
- **A common fix is adding a short random prefix or hash** to the start of busy keys, so requests spread more evenly.

> **Note:** OBS handles key distribution automatically in many cases. Use this guidance when you design for very high request rates, and check current OBS performance documentation.

---

## Part 8: Cost

OBS bills you for four things. Knowing them helps you find savings.

| Billing item | What it means | How to reduce it |
|---|---|---|
| **Storage usage** | How much data you keep | Delete old versions, use lifecycle rules |
| **Request count** | How many API calls you make | Batch operations, cache frequently read files |
| **Data retrieved** | Data read from Infrequent Access or Archive | Keep frequently read data in Standard |
| **Downstream traffic** | Data sent out of Huawei Cloud to users | Use a CDN to serve popular files closer to users |

---

## Part 9: Which Storage Do I Use?

Use this table as a starting point when you design a system.

| Question | If yes | If no |
|---|---|---|
| Does the server need a disk to install software or run a database? | EVS | Go on |
| Do several servers need to open the same folder at the same time, as normal files? | SFS | Go on |
| Is the data accessed through a URL or API, or stored once and read later? | OBS | Go on |

**ShopFast's final design:**
- Operating system and order database: **EVS**
- Return-form uploads being processed by several servers: **SFS**
- Product photos, backups, and invoices: **OBS**

---

## Part 10: ShopFast Storage Architecture

```
                         Internet
                             │
                             ▼
                   Elastic Load Balancer
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
     Web App 1 (AZ 1)                  Web App 2 (AZ 2)
     System disk: EVS                  System disk: EVS
            │                                 │
            └────────────────┬────────────────┘
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
        SFS: return-form         OBS bucket: shopfast-media
        uploads (shared)         product photos, invoices,
                                 backups (Standard, IA, Archive)
```

**How to read this:**
1. Each web server has its own system disk on EVS.
2. Uploads that several servers process go to a shared SFS folder.
3. Finished files such as product photos and invoices go to OBS, where the website and customers fetch them.

---

## Part 11: Quiz

Try these before the lecture ends. Answers will be discussed in class.

**Q1 (True/False):** In one bucket, two objects can have the same metadata values, but their keys must be unique.

**Q2 (Single choice):** ShopFast must keep yearly tax invoices for seven years. They are almost never opened. Which storage class fits best?
- A. OBS Standard
- B. OBS Infrequent Access
- C. OBS Archive
- D. EVS

**Q3 (Multiple choice):** Which statements about OBS are correct?
- A. New buckets and objects are private by default.
- B. Durability is 12 nines.
- C. An ECS can boot its operating system directly from an OBS bucket.
- D. Data can be accessed through HTTP or HTTPS APIs.

**Q4 (Single choice):** A yearly audit shows OBS costs are over budget. What is the best first step?
- A. Delete all objects
- B. Move everything to EVS
- C. Configure lifecycle rules to move older objects to cheaper classes
- D. Turn on versioning

**Q5 (Scenario):** A customer must download one private invoice, but the bucket must stay private. Which method should you use?

**Q6 (Scenario):** An editor uploads the wrong banner image and overwrites the good one. How can ShopFast recover the previous version?

---

## Glossary

| Term | Meaning |
|---|---|
| **Bucket** | A container for objects in OBS, with its own settings |
| **Block storage** | Storage that acts like a disk (EVS) |
| **CNAME** | A DNS record that points your domain to another address |
| **Delete marker** | A version-control marker that hides an object without erasing it |
| **Durability** | The chance that stored data is not lost |
| **EVS** | Elastic Volume Service: block storage disks |
| **File storage** | Storage shared as a folder (SFS) |
| **IAM** | Identity and Access Management: controls who can do what |
| **Key** | The unique name of an object within its bucket |
| **Lifecycle rule** | An automatic rule that moves or deletes objects by age |
| **Metadata** | Descriptive details attached to an object |
| **Object storage** | Storage accessed through web requests (OBS) |
| **Signed URL** | A temporary link that grants access for a set time |
| **Versioning** | Keeping every version of an object so earlier versions can be restored |

---

## Summary

- **Block (EVS)** acts like a disk for the OS and databases.
- **File (SFS)** acts like a shared folder for several servers.
- **Object (OBS)** stores files in buckets, identified by keys, and serves them over HTTP.
- **OBS** offers Standard, Infrequent Access, and Archive classes. Match the class to how often data is read.
- **Lifecycle rules and versioning** control cost and protect against mistakes.
- **Privacy** is the default. Use policies, IAM, or signed URLs to share access.

---

*This handout is based on Huawei Cloud's storage solution materials. Figures, limits, and features change, so confirm current details in the official Huawei Cloud documentation.*