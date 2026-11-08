# Knowledge Base: Software Installation Policy and Approved Applications

**Category:** Software  
**Tags:** software, installation, admin rights, privilege, approval, catalog, endpoint  
**Applicability:** All managed endpoint workstations (Windows, macOS, Linux)

---

## Overview
To prevent supply-chain malware and preserve system stability, standard user accounts do not possess local administrative privileges. Software is distributed via self-service package repositories.

## Approved Self-Service Catalogs
Employees can install pre-approved software without waiting for IT intervention:
- **Windows:** Open the **Company Portal** app from the Start Menu.
- **macOS:** Open **Jamf Self Service** from the Applications folder.
- **Pre-approved Catalog includes:** VS Code, Docker Desktop, PyCharm CE, Slack, Zoom, Google Chrome, Postman, Git, LibreOffice, and 7-Zip.

## Requesting Unlisted or Paid Commercial Software
1. Submit an IT Software Request ticket including:
   - Application Name and Exact Version.
   - Business Justification and manager approval email.
   - Vendor security documentation (SOC 2 Type II or ISO 27001 certification).
2. The IT Security Governance team reviews requests every Tuesday and Thursday.
3. Once approved, the software package is packaged and assigned to your device group within 24 hours.

## Temporary Local Administrator Access
Engineers requiring temporary root/admin access for local debugging or driver updates can request a 4-hour elevation ticket via the Privileged Access Management (PAM) portal at `https://pam.internal.corp`.
