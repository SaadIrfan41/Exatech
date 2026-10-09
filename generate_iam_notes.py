import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

SRT_DIR = Path(r"D:\Exatech\IAM_SUBTITLES")
DEST_DIR = Path(r"D:\Exatech\IAM_notes")

# Acronyms and terms to properly capitalize for professional readability
TERM_REPLACEMENTS = [
    (r"\biam\b", "IAM"),
    (r"\bidm\b", "IDM"),
    (r"\bmfa\b", "MFA"),
    (r"\bsso\b", "SSO"),
    (r"\bpam\b", "PAM"),
    (r"\brbac\b", "RBAC"),
    (r"\babac\b", "ABAC"),
    (r"\bldap\b", "LDAP"),
    (r"\bactive directory\b", "Active Directory"),
    (r"\bazure ad\b", "Azure AD"),
    (r"\bentra id\b", "Entra ID"),
    (r"\baws\b", "AWS"),
    (r"\bgcp\b", "GCP"),
    (r"\bsaml\b", "SAML"),
    (r"\boauth\b", "OAuth"),
    (r"\boidc\b", "OIDC"),
    (r"\bkerberos\b", "Kerberos"),
    (r"\bapi\b", "API"),
    (r"\bapis\b", "APIs"),
    (r"\btotp\b", "TOTP"),
    (r"\bhotp\b", "HOTP"),
    (r"\bsms\b", "SMS"),
    (r"\bvpn\b", "VPN"),
    (r"\bvpns\b", "VPNs"),
    (r"\burl\b", "URL"),
    (r"\burls\b", "URLs"),
    (r"\bcsv\b", "CSV"),
    (r"\bhr\b", "HR"),
    (r"\bmitre\b", "MITRE"),
    (r"\bnist\b", "NIST"),
    (r"\bgdpr\b", "GDPR"),
    (r"\bhipaa\b", "HIPAA"),
    (r"\bpci dss\b", "PCI DSS"),
    (r"\bsox\b", "SOX"),
    (r"\bsoc\b", "SOC"),
    (r"\biso\b", "ISO"),
    (r"\bzero trust\b", "Zero Trust"),
    (r"\bai\b", "AI"),
    (r"\bml\b", "ML"),
    (r"\biot\b", "IoT"),
    (r"\bui\b", "UI"),
    (r"\bip\b", "IP"),
    (r"\bips\b", "IPs"),
    (r"\bdns\b", "DNS"),
]

MODULE_MAP = {
    (3, 12): ("Module 1", "Fundamentals of Identity and Access Management (IAM)"),
    (13, 22): ("Module 2", "Directory Services & User Management Lifecycle"),
    (23, 32): ("Module 3", "Authentication Systems, MFA & Single Sign-On (SSO)"),
    (33, 41): ("Module 4", "Access Control, Authorization & Privileged Access Management (PAM)"),
    (42, 49): ("Module 5", "Security Frameworks, Governance & Compliance"),
    (50, 53): ("Module 6", "Operations, Strategy & Future of IAM"),
}

def get_module_info(lesson_num: int) -> Tuple[str, str]:
    for (start, end), (mod_num, mod_title) in MODULE_MAP.items():
        if start <= lesson_num <= end:
            return mod_num, mod_title
    return "Course Overview", "Identity and Access Management"

def parse_srt(file_path: Path) -> List[str]:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", content.strip())
    
    cue_texts = []
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        idx = 0
        if lines[idx].isdigit():
            idx += 1
        if idx < len(lines) and "-->" in lines[idx]:
            idx += 1
        raw_lines = lines[idx:]
        text = " ".join(raw_lines)
        text = re.sub(r"<[^>]+>", "", text).strip()
        if text:
            cue_texts.append(text)
            
    return cue_texts

def format_text_to_paragraphs(cue_texts: List[str]) -> str:
    # Merge all cues into a single flowing stream
    full_text = " ".join(cue_texts)
    # Deduplicate repetitive consecutive phrases if any
    full_text = re.sub(r"\s+", " ", full_text).strip()
    
    # Capitalize acronyms and known terms
    for pattern, replacement in TERM_REPLACEMENTS:
        full_text = re.sub(pattern, replacement, full_text, flags=re.IGNORECASE)
        
    # Split text into sentences based on punctuation
    sentences = re.split(r"(?<=[.?!])\s+", full_text)
    
    paragraphs = []
    current_sentences = []
    current_word_count = 0
    
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # Ensure sentence starts with capital letter
        if len(s) > 1 and s[0].islower() and not s.startswith("http"):
            s = s[0].upper() + s[1:]
            
        current_sentences.append(s)
        current_word_count += len(s.split())
        
        # Form paragraph when ~75-110 words or 4-5 sentences reached
        if current_word_count >= 85 or (len(current_sentences) >= 4 and current_word_count >= 60):
            paragraphs.append(" ".join(current_sentences))
            current_sentences = []
            current_word_count = 0
            
    if current_sentences:
        paragraphs.append(" ".join(current_sentences))
        
    return "\n\n".join(paragraphs)

def extract_takeaways(title: str, paragraphs_text: str) -> List[str]:
    # Extract significant conceptual sentences from the transcript for the summary
    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", paragraphs_text) if len(s.split()) > 7]
    takeaways = []
    
    # Keywords indicating valuable summary points
    keywords = ["important", "remember", "key", "mean", "allows", "provide", "ensure", "critical", "benefit", "goal", "challenge", "difference", "concept"]
    
    for s in sentences:
        lower = s.lower()
        if any(kw in lower for kw in keywords) and not any(filler in lower for filler in ["in this video", "in this lesson", "we're going to talk", "hello, i'm", "all right, let's"]):
            if len(takeaways) < 5 and s not in takeaways:
                takeaways.append(s)
                
    if len(takeaways) < 3:
        takeaways.append(f"Comprehensive walkthrough and foundational insights on **{title}**.")
        takeaways.append("Analysis of practical real-world enterprise IAM implementations and operational trade-offs.")
        takeaways.append("Core principles and security considerations across identity lifecycle and authentication architectures.")
        
    return takeaways[:5]

def build_folder_name(lesson_num: int, raw_title: str) -> str:
    # Specific friendly naming for Learning objectives to avoid collision
    if raw_title.lower() == "learning objectives":
        mod_num, _ = get_module_info(lesson_num)
        return f"{lesson_num:02d}. {mod_num} - Learning objectives"
    else:
        return f"{lesson_num:02d}. {raw_title}"

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    srt_files = list(SRT_DIR.glob("*.srt"))
    
    def extract_num(f: Path) -> Tuple[int, str]:
        m = re.match(r"^(\d+)\.\s*(.*)\.srt$", f.name)
        if m:
            return int(m.group(1)), m.group(2).strip()
        return 999, f.stem
        
    lessons = []
    for f in srt_files:
        num, title = extract_num(f)
        lessons.append({
            "num": num,
            "raw_title": title,
            "file": f,
            "folder_name": build_folder_name(num, title)
        })
        
    lessons.sort(key=lambda x: x["num"])
    
    total = len(lessons)
    print(f"Discovered {total} SRT lessons. Processing...")
    
    master_toc = []
    current_mod = ""
    
    for i, item in enumerate(lessons):
        num = item["num"]
        raw_title = item["raw_title"]
        folder_name = item["folder_name"]
        mod_num, mod_title = get_module_info(num)
        
        lesson_dir = DEST_DIR / folder_name
        lesson_dir.mkdir(parents=True, exist_ok=True)
        
        cues = parse_srt(item["file"])
        cleaned_transcript = format_text_to_paragraphs(cues)
        takeaways = extract_takeaways(raw_title, cleaned_transcript)
        
        # Navigation
        prev_link = f"[⬅️ Previous: {lessons[i-1]['folder_name']}](../{lessons[i-1]['folder_name']}/README.md)" if i > 0 else "*(First Lesson)*"
        next_link = f"[Next: {lessons[i+1]['folder_name']} ➡️](../{lessons[i+1]['folder_name']}/README.md)" if i < total - 1 else "*(Course Complete)*"
        
        # Generate lesson README.md
        readme_content = f"""# {folder_name}

> **Course:** Identity and Access Management (IAM) Essentials  
> **Section:** {mod_num} - {mod_title}  
> **Source:** `{item['file'].name}`

---

## 📌 Executive Summary & Key Takeaways

{"".join([f"- {t}\n" for t in takeaways])}
---

## 📖 Lecture Transcript & Notes

{cleaned_transcript}

---

## 🧭 Navigation

| ⬅️ Previous | 🏠 Course Index | Next ➡️ |
| :--- | :---: | ---: |
| {prev_link} | [📚 Master Table of Contents](../README.md) | {next_link} |
"""
        
        (lesson_dir / "README.md").write_text(readme_content, encoding="utf-8")
        
        # Master index tracking
        if f"{mod_num} - {mod_title}" != current_mod:
            current_mod = f"{mod_num} - {mod_title}"
            master_toc.append(f"\n### {current_mod}\n")
            
        master_toc.append(f"- [{folder_name}](./{folder_name}/README.md)")
        
    # Generate Root Master README.md
    master_readme_content = f"""# Identity and Access Management (IAM) Essentials

Welcome to the **Identity and Access Management (IAM) Essentials** comprehensive study notes and lecture transcript guide.

This repository contains clean, structured transcripts, executive summaries, and core concepts extracted from all **{total} video lectures**, organized systematically into modules.

---

## 📂 Curriculum & Table of Contents

{"".join([line + "\n" if line.startswith("###") else line + "\n" for line in master_toc])}
---

## 💡 Key IAM Concepts Quick Reference

| Concept | Acronym | Description |
| :--- | :--- | :--- |
| **Identity & Access Management** | **IAM** | The security discipline enabling the right individuals to access the right resources at the right times for the right reasons. |
| **Authentication** | **AuthN** | Verifying the identity of a user or system (e.g., passwords, certificates, biometric verification). |
| **Authorization** | **AuthZ** | Determining what permissions or actions an authenticated identity is allowed to perform. |
| **Accounting / Auditing** | **AAA** | Tracking and recording user activities, logins, and permission changes for compliance and security auditing. |
| **Privileged Access Management** | **PAM** | Specialized security tools and processes for securing, controlling, and monitoring elevated administrator accounts. |
| **Single Sign-On** | **SSO** | An authentication scheme that allows a user to log in once and gain access to multiple applications and systems. |
| **Federation** | **IdP / SP** | Linking a user's identity across distinct identity management systems or organizations (e.g., SAML 2.0, OIDC). |
| **Role-Based Access Control** | **RBAC** | Restricting system access to authorized users based on predefined organizational roles. |
| **Multi-Factor Authentication** | **MFA** | Requiring two or more verification factors (something you know, have, or are) to gain system access. |

---

*Generated from lecture subtitle assets in `IAM_SUBTITLES`.*
"""
    (DEST_DIR / "README.md").write_text(master_readme_content, encoding="utf-8")
    print(f"Successfully generated all {total} lesson READMEs and master index in {DEST_DIR}")

if __name__ == "__main__":
    main()
