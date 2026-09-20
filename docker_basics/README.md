# Docker From Zero: Virtualization, VMs, Kernels & Containers

Before touching Docker commands, it's worth understanding *why* Docker exists and what makes it different from a virtual machine. This guide builds that picture one idea at a time — everything after this will make a lot more sense once these fundamentals click.

```
What we'll build up to:
Virtualization → Hypervisors & VMs → What a kernel actually does →
Containers vs VMs → Docker on Linux → Docker on Windows (WSL 2) → Why it matters
```

---

## Step 1 — What is virtualization?

**Virtualization means using software to create a virtual version of a physical resource.**

Instead of giving software direct access to physical hardware, we create a software-based *representation* of that hardware.

Take one physical computer:

```
Physical Computer
┌─────────────────────────┐
│ CPU: 8 cores            │
│ RAM: 16 GB              │
│ Disk: 500 GB            │
└─────────────────────────┘
```

A **hypervisor** (virtualization software) can divide those resources into several virtual computers:

```
             Physical Computer
                    │
                Hypervisor
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       VM 1       VM 2       VM 3
       2 CPU      2 CPU      4 CPU
       4 GB       4 GB       8 GB
       Linux      Linux      Windows
```

Each VM behaves as if it's a separate physical computer, even though all three share the same underlying machine.

**Why "virtual"?** VM 1 doesn't actually have its own physical CPU, RAM, motherboard, or network card — the hypervisor creates *virtual* versions of these and hands them to the VM. The guest operating system inside the VM has no idea the hardware isn't really its own.

```
Physical CPU → Hypervisor → Virtual CPU → VM
```

---

## Step 2 — Virtualization is bigger than just VMs

You can virtualize more than just a whole computer:

```
Virtualization
│
├── Compute virtualization  → Virtual Machines
├── Network virtualization  → Virtual networks, switches, routers
├── Storage virtualization  → Virtual disks
└── OS-level virtualization → Containers
```

Keep that last line in mind — it's the key distinction we're building toward. Containers are a *different category* of virtualization than VMs, not just a smaller VM.

---

## Step 3 — How a VM actually runs

The full stack for a VM running on your own laptop looks like this:

```
Physical Hardware
       ↓
    Windows
       ↓
   Hypervisor
       ↓
   Virtual Machine
       ↓
 Guest OS (Linux)
       ↓
 Applications
```

For example, on a Windows laptop:

```
Windows 11
    │
    └── VMware Workstation
            │
            └── Ubuntu VM
                    │
                    └── FastAPI application
```

The Ubuntu VM believes it has its own CPU, RAM, disk, and network card — but these are all virtual resources handed to it by the hypervisor.

---

## Step 4 — Popular hypervisors

| Hypervisor | Common use |
|---|---|
| VMware ESXi | Enterprise / cloud servers |
| Microsoft Hyper-V | Windows / enterprise |
| KVM | Linux servers, very common in the cloud |
| VirtualBox | Desktop / lab / testing |
| VMware Workstation | Desktop / lab / testing |
| Xen | Cloud / servers, historically important |

---

## Step 5 — Two types of hypervisors

**Type 1 — Bare-metal:** runs directly on the hardware, no host OS underneath it.

```
Hardware
   ↓
Hypervisor
   ↓
VMs
```

Examples: VMware ESXi, Hyper-V, KVM, Xen. Very common in data centers and cloud computing — e.g. a cloud provider might run:

```
Physical Server
       ↓
     KVM
       ↓
 ┌─────┼─────┐
 ↓     ↓     ↓
VM1   VM2   VM3
```

**Type 2 — Hosted:** the hypervisor runs on top of an existing OS.

```
Hardware
   ↓
Windows
   ↓
VirtualBox / VMware Workstation
   ↓
Ubuntu VM
```

This is what you'll typically see on a developer's laptop.

---

## Step 6 — What is a kernel?

To understand why containers are different from VMs, we need to understand what a **kernel** actually is.

**The kernel is the core part of an operating system that controls and manages the computer's hardware.** It's the middleman between your applications and the physical hardware:

```
Applications
     ↓
  OS / Kernel
     ↓
  Hardware
```

Example: when a Python program wants to save a file, it doesn't touch the disk directly — it asks the kernel:

```
Python program
     ↓
"Please save this file"
     ↓
   Kernel
     ↓
Disk
```

---

## Step 7 — What the kernel is responsible for

**CPU management** — many programs want CPU time at once (Chrome, VS Code, Python, Docker, Spotify...). The kernel decides who runs when. This is called **process scheduling**.

**Memory management** — the kernel decides which processes get which chunks of RAM, and protects one process from reading or writing another's memory.

```
16 GB RAM
 ├── Chrome → 4 GB
 ├── VS Code → 2 GB
 ├── Docker → 3 GB
 └── Other → 7 GB
```

**Hardware management** — disks, keyboards, network cards, USB devices, GPUs. The kernel talks to these through **device drivers**:
```
Application → Kernel → Driver → Hardware
```

**Networking** — the kernel's networking stack handles TCP/IP, sockets, routing, and interfaces when your app sends data:
```
FastAPI → Kernel networking stack → Network driver → Network card → Internet
```

**Filesystems** — when you run `open("hello.txt", "w")` in Python, ultimately the kernel is the one interacting with the storage hardware on your behalf.

---

## Step 8 — System calls (the important concept)

Applications don't talk to hardware directly — they ask the kernel through **system calls**.

```
Python
  │
  │ system call
  ↓
Kernel
  │
  ↓
Hardware
```

Think of a system call as: *"Kernel, please do this operation for me."* Creating a process, opening a file, reading/writing data, using the network, allocating memory — all of these go through the kernel.

This is the concept that unlocks *why* containers work the way they do — keep it in mind for the next step.

---

## Step 9 — Containers vs VMs: the real difference

A VM contains an entire **guest operating system**, including its own kernel:

```
VM
├── Linux kernel
├── system libraries
├── application
└── dependencies
```

A **container** does not have its own kernel — it shares the **host's kernel**:

```
Host Linux Kernel
       │
   ┌───┼────┐
   ↓   ↓    ↓
  C1  C2    C3
   │   │     │
 App  App   App
```

So instead of:
```
Hardware → Hypervisor → VM → Guest OS → Application
```
Docker does:
```
Hardware → Host OS → Container Runtime → Container → Application
```

Say you run:
```bash
docker run nginx
```
nginx needs CPU, memory, filesystem, and networking — but it doesn't control any of that directly. It runs as a regular process and makes system calls to the same Linux kernel every other container (and the host itself) is using:

```
                Linux
┌──────────────────────────────────┐
│  Container 1       Container 2   │
│  ┌───────────┐     ┌───────────┐ │
│  │   nginx   │     │  FastAPI  │ │
│  └─────┬─────┘     └─────┬─────┘ │
│        │                  │       │
│        └────────┬─────────┘       │
│                 ↓                 │
│          Linux Kernel             │
│                 ↓                 │
│             Hardware              │
└──────────────────────────────────┘
```

**This is the single most important distinction to remember:** a VM has its own kernel; a container borrows the host's.

---

## Step 10 — How Docker achieves this on Linux

Docker doesn't need a hypervisor or a VM on Linux. It uses features already built into the Linux kernel:

```
Linux
 │
 ├── Docker Engine
 │      │
 │      ├── Container 1
 │      ├── Container 2
 │      └── Container 3
 │
 └── Linux Kernel
```

- **Namespaces** → give each container the illusion of having its own isolated view of processes, network, etc.
- **cgroups** → limit how much CPU/memory each container can use.
- **Union/overlay filesystems** → build up a container's filesystem in efficient, reusable layers.

Containers are simply isolated processes on the same kernel — not separate virtual machines.

---

## Step 11 — Docker Desktop on Windows (WSL 2)

Windows has its own kernel, not a Linux one — but almost all Docker containers you'll use are **Linux containers**, which need a Linux kernel to run on.

That's what **WSL 2** (Windows Subsystem for Linux 2) provides: a real Linux kernel, running inside a lightweight virtualized environment.

```
Physical Hardware
       ↓
    Windows
       ↓
Virtualization / Hyper-V technology
       ↓
   WSL 2 Linux environment
       ↓
   Linux Kernel
       ↓
   Docker Engine
       ↓
 ┌─────┼─────┐
 ↓     ↓     ↓
C1    C2    C3
```

**Important clarification:** WSL 2 gives you *one* Linux kernel. Docker Desktop then runs all your containers on top of that single shared kernel — the containers still don't each get their own kernel; they share the one WSL 2 provides.

```
                 Windows
                    │
             WSL 2 Linux VM
                    │
             ┌──────┴──────┐
             │ Linux Kernel│
             └──────┬──────┘
                    │
              Docker Engine
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    Container    Container    Container
      nginx       FastAPI       Redis
```

**This does not mean each container is a VM.** The Linux *environment* is virtualized (that's WSL 2's job); the containers inside it are still lightweight containers sharing that one Linux kernel — exactly like Step 9 and Step 10 described.

---

## Step 12 — Side-by-side: VMs vs containers

**VMs — each has its own kernel:**
```
Hardware
   ↓
Hypervisor
   ↓
┌───────────────┐   ┌───────────────┐
│ VM 1          │   │ VM 2          │
│ Linux Kernel  │   │ Linux Kernel  │
└───────────────┘   └───────────────┘
```

**Containers — all share one kernel:**
```
Hardware
   ↓
Linux Kernel
   ↓
┌────────┬────────┬────────┐
│ C1     │ C2     │ C3     │
│ nginx  │ FastAPI│ Redis  │
└────────┴────────┴────────┘
```

This is exactly why containers start up faster and use far fewer resources than VMs — a container never has to boot up its own operating system:

```
VM:         Application + Libraries + User space + its own Linux kernel
Container:  Application + Libraries + Filesystem → shared Linux kernel
```

---

## Step 13 — A simple mental model

Think of a **VM as renting an entire apartment**:
```
Building
 ├── Apartment 1 → its own kitchen, bathroom, everything
 ├── Apartment 2 → its own kitchen, bathroom, everything
```
Each VM gets its own complete operating system.

Think of **containers as rooms in the same building**:
```
Building / OS
 ├── Room → Container 1
 ├── Room → Container 2
 └── Room → Container 3
```
They share the underlying infrastructure (the kernel) but are still isolated from one another.

---

## Step 14 — Why Docker is actually useful

Without Docker, running your FastAPI app somewhere else means reproducing your entire environment by hand:

```
Your computer
 ├── Python 3.12
 ├── FastAPI
 ├── dependencies
 ├── environment variables
 └── your application
```

With Docker, all of that gets packaged into one portable **image**:

```
Docker Image
 ├── Python
 ├── FastAPI
 ├── dependencies
 └── your application
```

```
Docker Image → Container → FastAPI
```

And that exact image can move anywhere:

```
Developer Laptop → Image → Cloud Server → Container → FastAPI
```

Same image, same behavior, wherever it runs.

---

## The one sentence to remember

> A hypervisor virtualizes hardware to run virtual machines, each with its own kernel. Docker/containerization isolates applications at the operating-system level, usually sharing the host's single kernel.

---

## Step 15 — One more connection: containers and VMs together

In cloud environments (AWS, Azure, Huawei Cloud), these two ideas aren't mutually exclusive — they're often stacked:

```
VMware / KVM / Hyper-V
        ↓
   Virtual Machines
        ↓
      Linux
        ↓
 Docker / containerd
        ↓
    Containers
        ↓
   Applications
```

This is exactly why **Kubernetes normally runs containers, but those containers are often themselves running inside VMs** on a cloud provider's infrastructure — the two layers of virtualization stack on top of each other.

---

## Recap

```
Virtualization (the general idea)
   ↓
Hypervisors → create Virtual Machines, each with its own kernel
   ↓
Kernel → the core of an OS: manages CPU, memory, hardware, networking, filesystems
   ↓
System calls → how applications ask the kernel to do things
   ↓
Containers → isolated processes sharing one host kernel (not full VMs)
   ↓
Docker on Linux → uses namespaces, cgroups, overlay filesystems directly
   ↓
Docker on Windows → WSL 2 provides one shared Linux kernel for all containers
```

## Quick-reference glossary

| Term | Meaning |
|---|---|
| **Virtualization** | Using software to create a virtual version of a physical resource |
| **Hypervisor** | Software that creates and runs virtual machines |
| **Virtual Machine (VM)** | A simulated computer with its own complete guest OS and kernel |
| **Type 1 hypervisor** | Runs directly on hardware (bare-metal) — e.g. KVM, ESXi |
| **Type 2 hypervisor** | Runs on top of a host OS — e.g. VirtualBox, VMware Workstation |
| **Kernel** | The core of an OS; manages CPU, memory, hardware, networking, filesystems |
| **System call** | A request an application makes to the kernel to perform an operation |
| **Process scheduling** | How the kernel decides which process gets CPU time, and when |
| **Namespace** | Linux kernel feature giving a container an isolated view of resources |
| **cgroups** | Linux kernel feature that limits CPU/memory usage per container |
| **Container** | An isolated process sharing the host machine's single kernel |
| **Container runtime** | The software (e.g. Docker Engine) that creates and runs containers |
| **WSL 2** | Windows Subsystem for Linux v2 — provides a real Linux kernel on Windows |
| **Image** | A packaged snapshot of an app and everything it needs to run |