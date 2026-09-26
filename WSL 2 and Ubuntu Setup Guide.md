# **Complete Guide: Installing WSL 2 & Ubuntu on Windows 11**

# **Overview**

This guide covers the full step-by-step process to enable hardware virtualization, install Windows Subsystem for Linux (WSL 2), set up Ubuntu, manage Linux distributions, and understand WSL state behavior, including why distributions show as Stopped.

# **Step 1: Check Hardware Virtualization**

WSL 2 requires CPU virtualization to be enabled in your system's firmware/BIOS.

1. Open **Task Manager** (`Ctrl + Shift + Esc`).  
2. Go to the **Performance** tab and select **CPU** on the left panel.  
3. Check the **Virtualization** field near the bottom right:  
   * If **Enabled**, proceed to Step 2\.  
   * If **Disabled**, restart your PC, enter BIOS/UEFI settings, and enable Intel VT-x or AMD-V.

# **Step 2: Enable WSL & Download Kernel**

1. Open **Start Menu**, search for **PowerShell**, right-click it, and select **Run as Administrator**.  
2. Run the following command:  
   `wsl --install`  
3. Restart your computer when prompted to complete the installation of Virtual Machine Platform components.

# **Step 3: Verify WSL Setup & List Available Distributions**

1. Open **PowerShell** as Administrator after rebooting.  
2. Check installed distributions:  
   `wsl --list --verbose`  
3. View available distributions online:  
   `wsl --list --online`

# **Step 4: Install Ubuntu & Set Up User Account**

1. Install Ubuntu:  
   `wsl --install -d Ubuntu`  
2. Once setup completes, the Ubuntu terminal will open automatically.  
3. Enter a new Linux username and password when prompted.

# **Step 5: Launching & Managing Ubuntu**

## **Launch Options**

* Open **Start Menu** \-\> Search and click **Ubuntu**.  
* Or open **Windows Terminal**, click the drop-down menu at the top, and select **Ubuntu**.  
* Or run `wsl -d Ubuntu` in Command Prompt / PowerShell.

## **Check Version & Release**

Inside the Ubuntu terminal, run:  
`lsb_release -a`

## **Update WSL Platform & Packages**

* **Update WSL Kernel** (in PowerShell):  
  `wsl --update`  
* **Update Ubuntu packages** (in Ubuntu terminal):  
  `sudo apt update && sudo apt upgrade -y`

# **Step 6: Understanding WSL Distribution States (`Stopped` vs `Running`)**

## **Why does `wsl --list --verbose` show distributions as `Stopped`?**

When running wsl \--list \--verbose, you might see distributions like Ubuntu, rancher-desktop, or `docker-desktop` listed with state **`Stopped`**.

* **This is expected and normal behavior:** WSL 2 distributions are lightweight virtual environments that automatically shut down when there are no active terminal sessions or running background tasks. This conserves system memory (RAM) and CPU resources.  
* **How to start a stopped distribution:** Simply launch it via the terminal or Start Menu (e.g., running `wsl` or `wsl -d Ubuntu`). Its state will immediately change to **`Running`**.

# **Step 7: File System Integration & Utilities**

* **Accessing Windows files from Ubuntu:** Windows drives are mounted under `/mnt/` (e.g., `/mnt/c/`).  
* **Accessing Linux files from Windows:** Open Windows File Explorer and navigate to `\\wsl$\` or click the **Linux** item in the left sidebar.  
* **Launch Windows apps from Ubuntu:**  
  `notepad.exe ~/.bashrc`  
* **Execute Linux commands from PowerShell:**  
  `wsl ls -la`

