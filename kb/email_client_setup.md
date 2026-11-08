# Knowledge Base: Corporate Email Setup for Outlook, Apple Mail, and Mobile

**Category:** Software  
**Tags:** email, outlook, exchange, software, imap, oauth2, sync, mailbox, office365  
**Applicability:** Microsoft Outlook 365, Apple Mail, iOS/Android Outlook

---

## Overview
All corporate email accounts are hosted on Microsoft 365 Exchange Online. Basic authentication (POP3/plain IMAP) is permanently disabled in favor of Modern Authentication with OAuth2 and conditional access policies.

## Outlook Desktop Client Synchronization Errors

### 1. Outlook Stuck on "Trying to connect..." or "Disconnected"
1. Verify internet connectivity and test browsing to `https://outlook.office.com`.
2. If webmail works, close Outlook completely.
3. Open Windows Run (`Win + R`) and launch Outlook in safe mode:
   ```cmd
   outlook.exe /safe
   ```
4. If Outlook connects in safe mode, an installed add-in (such as CRM or antivirus plugins) is causing an RPC lock. Disable suspect add-ins under **File > Options > Add-ins**.

### 2. Corrupt Outlook Data File (.OST)
When emails fail to sync or folders show outdated content:
1. Exit Outlook.
2. Navigate to: `%localappdata%\Microsoft\Outlook`
3. Locate the file named `your.email@example.com.ost` and rename it to `your.email@example.com.ost.old`.
4. Re-open Outlook. The application will automatically recreate the OST file and download fresh server headers and messages.

### 3. Mobile Device Configuration (iOS & Android)
- **Approved Client:** Microsoft Outlook app downloaded from the Managed Google Play or Apple App Store.
- Open Outlook, enter your corporate email, and authorize via Company SSO / Authenticator.
- Built-in Apple Mail or Samsung Mail is only supported if enrolled via corporate MDM profile.
