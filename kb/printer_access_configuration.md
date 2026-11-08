# Knowledge Base: Network Printer Setup and Secure Badge Release Printing

**Category:** Hardware  
**Tags:** printer, printing, hardware, network, papercut, driver, queue, badge  
**Applicability:** All corporate campus facilities and shared multi-function printers (MFDs)

---

## Overview
All physical corporate offices use PaperCut FollowMe printing. Rather than printing directly to a local device, print jobs are sent to a virtual queue and released at any office printer using your employee RFID badge.

## Connecting to the Global Print Queue

### Windows Configuration
1. Press `Win + R` to open the Run dialog.
2. Enter the corporate print spooler path:
   ```cmd
   \\printcorp.internal.corp\FollowMe-Color
   ```
3. When prompted, enter your domain credentials (`CORP\username` and password).
4. Windows will automatically download and install the certified Universal PostScript driver.
5. Set `FollowMe-Color` as your default printer in **Settings > Bluetooth & devices > Printers & scanners**.

### macOS Configuration
1. Open **System Settings > Printers & Scanners**.
2. Click **Add Printer, Scanner, or Fax**.
3. Select the **IP** tab (Globe icon).
4. Address: `printcorp.internal.corp`
5. Protocol: **Line Printer Daemon - LPD**
6. Queue: `FollowMe-Color`
7. Name: `Corporate FollowMe Printing`
8. Use: Select **Generic PostScript Printer** with duplex unit enabled.

## Releasing Print Jobs at the MFD
1. Walk up to any Ricoh / Canon office printer.
2. Tap your physical employee badge against the contactless card reader.
3. Select your queued jobs on the touchscreen and press **Print All**.
4. Remember to press **Log Out** when finished to safeguard confidential printed materials.
