# Knowledge Base: GlobalProtect and OpenVPN Client Troubleshooting

**Category:** Network  
**Tags:** vpn, globalprotect, openvpn, network, gateway error, authentication, remote access  
**Applicability:** Windows 10/11, macOS, Linux workstations

---

## Overview
Remote employees use corporate VPN gateways to securely access internal resources. Connection issues typically stem from cached authentication tokens, stale DNS entries, or local firewall/router interference.

## Common Symptoms
- Gateway Connection Timeout: The client remains stuck at "Connecting" or reports "Could not connect to gateway".
- Authentication Failed: Prompts for credentials repeatedly or reports invalid portal credentials despite correct SSO password.
- Split-Tunnel Failure: Internal intranet sites or databases fail to resolve while external internet sites load normally.

## Step-by-Step Resolution

### 1. Refresh Authentication and Portal Configuration
1. Open the **GlobalProtect** (or OpenVPN) client from the system tray or menu bar.
2. Click the gear / Settings icon and select **Settings > General**.
3. Under the portal address (`vpn.internal.corp`), click **Refresh Connection**.
4. When prompted by the SSO web browser pop-up, complete multi-factor authentication (MFA) via the company Authenticator app.

### 2. Flush Local DNS Cache
Stale DNS resolvers frequently prevent internal DNS servers from taking precedence over home router DNS.
- **Windows:**
  ```powershell
  ipconfig /flushdns
  ipconfig /registerdns
  ```
- **macOS:**
  ```bash
  sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
  ```

### 3. Reinstall / Reset Network Adapter
If the virtual network adapter (TAP or PANGP Virtual Ethernet Adapter) shows a yellow warning icon in Device Manager:
1. Open Windows Device Manager > Network Adapters.
2. Right-click **PANGP Virtual Ethernet Adapter** and choose **Disable device**, wait 5 seconds, then **Enable device**.
3. Reboot the computer if the virtual adapter fails to obtain a 10.x.x.x IP address.

### 4. Router MTU Configuration
If VPN disconnects under heavy data transfer, set the local router MTU to 1420 or lower to prevent packet fragmentation over residential broadband.

---
*For persistent gateway unreachable errors outside business hours, check the IT Status Page at `https://status.internal.corp` for active outages before escalating.*
