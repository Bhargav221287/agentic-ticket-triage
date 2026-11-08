# Knowledge Base: Slack and Zoom Audio/Video Permissions and Sync

**Category:** Software  
**Tags:** slack, zoom, software, microphone, camera, audio, permissions, screen sharing  
**Applicability:** macOS (Sequoia / Sonoma / Ventura), Windows 10/11

---

## Overview
Issues with microphone access, missing webcams, screen sharing authorization, or lagging notifications in Slack and Zoom usually stem from OS-level privacy permissions or hardware acceleration incompatibilities.

## Resolving Camera & Microphone Access

### 1. macOS Privacy Settings
If Zoom or Slack displays "Cannot access microphone/camera":
1. Open **System Settings > Privacy & Security**.
2. Click **Microphone** and toggle the switch ON for **Zoom Workplace** and **Slack**.
3. Click **Camera** and toggle ON.
4. Click **Screen & System Audio Recording** and verify Slack and Zoom are permitted.
5. If toggles are grayed out, quit the app completely (`Cmd + Q`) and relaunch to prompt the OS permission dialog.

### 2. Windows 11 Privacy Settings
1. Go to **Settings > Privacy & security > Microphone**.
2. Ensure **Microphone access** is turned ON.
3. Ensure **Let apps access your microphone** and **Let desktop apps access your microphone** are both toggled ON.
4. Repeat the same verification under **Camera** settings.

## Audio Driver and Peripheral Selection in Zoom
- Inside Zoom: Go to **Settings > Audio**.
- Set **Speaker** and **Microphone** to the specific physical headset (e.g., "Jabra Evolve2") instead of "Same as System", which can become confused when docking/undocking.
- Disable "Automatically adjust microphone volume" if voice cuts out during speech.

## Slack Cache Cleanup
If messages fail to load or unread badges are out of sync:
- In Slack, press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (macOS) to reload.
- Go to **Help > Troubleshooting > Clear Cache and Restart**.
