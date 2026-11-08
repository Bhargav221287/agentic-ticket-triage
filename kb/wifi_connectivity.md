# Knowledge Base: Corporate Wi-Fi (CorpNet-Secure) Setup and Diagnostics

**Category:** Network  
**Tags:** wifi, wireless, corpnet, network, 802.1x, radius, certificate, connection drop  
**Applicability:** All corporate-managed laptops and authorized mobile devices

---

## Overview
The corporate wireless network `CorpNet-Secure` uses WPA3-Enterprise (802.1X EAP-TLS) with device certificates provisioned automatically via Mobile Device Management (Intune / Jamf).

## Available Wireless Networks
1. **CorpNet-Secure:** Encrypted internal Wi-Fi for managed devices only. Grants access to internal development clusters, file shares, and intranet.
2. **Corp-Guest:** Isolated internet-only access for visitors and personal phones. Requires daily web portal terms acceptance.

## Common Connection Issues & Fixes

### 1. "Cannot connect to this network" or Certificate Expired
1. Check if the device client certificate is valid:
   - On Windows: Run `certmgr.msc`, inspect **Personal > Certificates**, looking for `issued by Internal Root CA`.
   - On macOS: Open **Keychain Access**, check **System > Certificates**.
2. If expired, connect temporarily to `Corp-Guest`, open the **Company Portal** app, and click **Check device status** / **Sync** to pull a renewed certificate.

### 2. Forget and Re-add Network Profile
If cached credentials conflict with updated security settings:
- **Windows:**
  ```powershell
  netsh wlan delete profile name="CorpNet-Secure"
  ```
- **macOS:**
  Go to **System Settings > Wi-Fi > Known Networks**, click `...` next to `CorpNet-Secure`, and select **Forget This Network**.
- Reconnect and select certificate authentication when prompted.

### 3. Wi-Fi Adapter Power Saving
On Windows laptops experiencing random disconnects when running on battery:
1. Open **Device Manager > Network Adapters > [Intel Wi-Fi 6] > Properties**.
2. Click the **Power Management** tab.
3. Uncheck **"Allow the computer to turn off this device to save power"**.
