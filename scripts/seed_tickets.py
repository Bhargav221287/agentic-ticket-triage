"""Seed script to populate SQLite database with 10 realistic sample IT support tickets."""

import os
import sys
from datetime import datetime, timedelta

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal, init_db
from app.models import Ticket, AgentLog, Approval


def seed_tickets() -> None:
    """Insert 10 diverse sample tickets covering various categories and workflow states."""
    init_db()
    db = SessionLocal()

    try:
        # Check if tickets already exist
        existing_count = db.query(Ticket).count()
        if existing_count >= 10:
            print(f"Database already contains {existing_count} tickets. Skipping seeding.")
            return

        now = datetime.utcnow()

        sample_tickets = [
            # 1. Resolved Network / VPN ticket
            {
                "customer_name": "Marcus Vance",
                "customer_email": "marcus.vance@example.com",
                "subject": "GlobalProtect VPN gateway authentication failed after password change",
                "description": "I updated my corporate password this morning. Now when GlobalProtect tries to connect to vpn.internal.corp, it fails with Gateway Error 403.",
                "category": "network",
                "priority": "high",
                "status": "resolved",
                "classifier_confidence": 0.94,
                "resolver_confidence": 0.92,
                "review_status": "auto_send",
                "draft_resolution": (
                    "Hello Marcus,\n\nFollowing your password change, the VPN client retains a cached session token. "
                    "Please open GlobalProtect, go to Settings > General > Portal (vpn.internal.corp), and click 'Refresh Connection'. "
                    "Complete the web MFA prompt to store your renewed credentials.\n\nBest regards,\nIT Service Desk"
                ),
                "final_resolution": (
                    "Hello Marcus,\n\nFollowing your password change, the VPN client retains a cached session token. "
                    "Please open GlobalProtect, go to Settings > General > Portal (vpn.internal.corp), and click 'Refresh Connection'. "
                    "Complete the web MFA prompt to store your renewed credentials.\n\nBest regards,\nIT Service Desk"
                ),
                "created_at": now - timedelta(days=5),
            },
            # 2. Resolved Access / Password Reset ticket
            {
                "customer_name": "Elena Rostova",
                "customer_email": "elena.rostova@example.com",
                "subject": "Locked out of Active Directory account after returning from vacation",
                "description": "Entered wrong password multiple times on my desktop. Account is locked. Need immediate access to join client meeting.",
                "category": "access",
                "priority": "high",
                "status": "resolved",
                "classifier_confidence": 0.96,
                "resolver_confidence": 0.95,
                "review_status": "auto_send",
                "draft_resolution": (
                    "Hello Elena,\n\nYour account has entered the standard 30-minute lock protection. You can unlock it immediately "
                    "by visiting our self-service portal: https://identity.internal.corp/unlock and completing your Authenticator push challenge. "
                    "Per IT security policy, support agents will never ask for your password.\n\nBest regards,\nIT Service Desk"
                ),
                "final_resolution": (
                    "Hello Elena,\n\nYour account has entered the standard 30-minute lock protection. You can unlock it immediately "
                    "by visiting our self-service portal: https://identity.internal.corp/unlock and completing your Authenticator push challenge. "
                    "Per IT security policy, support agents will never ask for your password.\n\nBest regards,\nIT Service Desk"
                ),
                "created_at": now - timedelta(days=4),
            },
            # 3. Resolved Hardware / External Display ticket
            {
                "customer_name": "David Kim",
                "customer_email": "david.kim@example.com",
                "subject": "Dual Dell monitors flickering black when plugged into Thunderbolt dock",
                "description": "My secondary 4K display goes black every 15 seconds when connected through the WD19TB docking station over DisplayPort.",
                "category": "hardware",
                "priority": "medium",
                "status": "resolved",
                "classifier_confidence": 0.91,
                "resolver_confidence": 0.89,
                "review_status": "auto_send",
                "draft_resolution": (
                    "Hello David,\n\nThis is commonly caused by dock capacitor saturation or display refresh rate mismatch. "
                    "1. Perform a hard dock reset: disconnect the dock from laptop and power outlet, hold the dock power button for 30s, then reconnect power. "
                    "2. In Windows Display Settings, ensure both monitors are locked to 60 Hz.\n\nBest regards,\nIT Service Desk"
                ),
                "final_resolution": (
                    "Hello David,\n\nThis is commonly caused by dock capacitor saturation or display refresh rate mismatch. "
                    "1. Perform a hard dock reset: disconnect the dock from laptop and power outlet, hold the dock power button for 30s, then reconnect power. "
                    "2. In Windows Display Settings, ensure both monitors are locked to 60 Hz.\n\nBest regards,\nIT Service Desk"
                ),
                "created_at": now - timedelta(days=3),
            },
            # 4. Resolved Software / Outlook OST Corrupted
            {
                "customer_name": "Amina Patel",
                "customer_email": "amina.patel@example.com",
                "subject": "Outlook stuck at 'Updating Inbox' and emails not sending",
                "description": "My Microsoft Outlook client is stuck synchronizing folder Inbox for 2 days. Webmail works fine.",
                "category": "software",
                "priority": "medium",
                "status": "resolved",
                "classifier_confidence": 0.92,
                "resolver_confidence": 0.90,
                "review_status": "auto_send",
                "draft_resolution": (
                    "Hello Amina,\n\nYour local cached Exchange data file (.OST) is likely corrupted. "
                    "Exit Outlook, navigate to %localappdata%\\Microsoft\\Outlook, rename your email .ost file to .old, and restart Outlook. "
                    "It will rebuild the cache automatically from Exchange Online.\n\nBest regards,\nIT Service Desk"
                ),
                "final_resolution": (
                    "Hello Amina,\n\nYour local cached Exchange data file (.OST) is likely corrupted. "
                    "Exit Outlook, navigate to %localappdata%\\Microsoft\\Outlook, rename your email .ost file to .old, and restart Outlook. "
                    "It will rebuild the cache automatically from Exchange Online.\n\nBest regards,\nIT Service Desk"
                ),
                "created_at": now - timedelta(days=3),
            },
            # 5. Pending Approval - Critical Security Incident
            {
                "customer_name": "Gregory House",
                "customer_email": "gregory.house@example.com",
                "subject": "CRITICAL: Multiple workstations receiving encrypted ransom notes in Finance",
                "description": "Shared folder files have turned into .locked extensions and a text note demands contact. We suspect active ransomware.",
                "category": "access",
                "priority": "critical",
                "status": "pending_approval",
                "classifier_confidence": 0.99,
                "resolver_confidence": 0.91,
                "review_status": "needs_human_approval",
                "draft_resolution": (
                    "URGENT INCIDENT RESPONSE PROTOCOL:\n"
                    "1. Immediately disconnect all affected machines from Wi-Fi and pull out Ethernet cables.\n"
                    "2. DO NOT restart or power off machines to preserve forensic RAM.\n"
                    "3. Security Incident Team is responding via phone now."
                ),
                "final_resolution": None,
                "created_at": now - timedelta(hours=2),
            },
            # 6. Pending Approval - Low Confidence Hardware issue
            {
                "customer_name": "Chloe Bennett",
                "customer_email": "chloe.bennett@example.com",
                "subject": "Laptop chassis making high pitched buzzing sound near the fan vent",
                "description": "Weird coil whine or buzzing noise when running GPU intensive tasks. Laptop feels warm.",
                "category": "hardware",
                "priority": "medium",
                "status": "pending_approval",
                "classifier_confidence": 0.78,
                "resolver_confidence": 0.62,
                "review_status": "needs_human_approval",
                "draft_resolution": (
                    "Hello Chloe,\n\nPlease run hardware diagnostics in BIOS (press F12 on boot) and verify fan thermal performance. "
                    "If fan bearings have failed, visit IT Service Bar for fan module replacement."
                ),
                "final_resolution": None,
                "created_at": now - timedelta(hours=4),
            },
            # 7. Resolved Network / Wi-Fi CorpNet 802.1x
            {
                "customer_name": "Liam O'Connor",
                "customer_email": "liam.oconnor@example.com",
                "subject": "MacBook cannot connect to CorpNet-Secure Wi-Fi in London office",
                "description": "Wi-Fi prompts for certificate, but clicking Connect gives 'Authentication failed'.",
                "category": "network",
                "priority": "medium",
                "status": "resolved",
                "classifier_confidence": 0.93,
                "resolver_confidence": 0.91,
                "review_status": "auto_send",
                "draft_resolution": (
                    "Hello Liam,\n\nYour device authentication certificate in macOS Keychain has expired. Connect to Corp-Guest, "
                    "open the Company Portal app, and click 'Check Status' to sync and download the latest 802.1X identity profile.\n\n"
                    "Best regards,\nIT Service Desk"
                ),
                "final_resolution": (
                    "Hello Liam,\n\nYour device authentication certificate in macOS Keychain has expired. Connect to Corp-Guest, "
                    "open the Company Portal app, and click 'Check Status' to sync and download the latest 802.1X identity profile.\n\n"
                    "Best regards,\nIT Service Desk"
                ),
                "created_at": now - timedelta(days=2),
            },
            # 8. Resolved Software / Zoom camera permission
            {
                "customer_name": "Sophia Zhang",
                "customer_email": "sophia.zhang@example.com",
                "subject": "Zoom shows black screen for webcam on macOS Sequoia",
                "description": "Built-in FaceTime camera works in Photo Booth but Zoom says camera is unavailable or in use by another application.",
                "category": "software",
                "priority": "low",
                "status": "resolved",
                "classifier_confidence": 0.90,
                "resolver_confidence": 0.89,
                "review_status": "auto_send",
                "draft_resolution": (
                    "Hello Sophia,\n\nmacOS Sequoia privacy permissions frequently require re-authorization after updates. "
                    "Open System Settings > Privacy & Security > Camera, toggle Zoom Workplace OFF and ON, then restart Zoom.\n\n"
                    "Best regards,\nIT Service Desk"
                ),
                "final_resolution": (
                    "Hello Sophia,\n\nmacOS Sequoia privacy permissions frequently require re-authorization after updates. "
                    "Open System Settings > Privacy & Security > Camera, toggle Zoom Workplace OFF and ON, then restart Zoom.\n\n"
                    "Best regards,\nIT Service Desk"
                ),
                "created_at": now - timedelta(days=1),
            },
            # 9. Resolved Hardware / Badge Printer PaperCut
            {
                "customer_name": "Carlos Gomez",
                "customer_email": "carlos.gomez@example.com",
                "subject": "Cannot print to 3rd floor office printer from new Windows 11 laptop",
                "description": "Printer is not showing in Windows print dialog. How do I add the FollowMe campus print queue?",
                "category": "hardware",
                "priority": "low",
                "status": "resolved",
                "classifier_confidence": 0.91,
                "resolver_confidence": 0.92,
                "review_status": "auto_send",
                "draft_resolution": (
                    "Hello Carlos,\n\nTo connect to the universal badge printing spooler, press Win + R and enter: "
                    "\\\\printcorp.internal.corp\\FollowMe-Color. Authenticate with your CORP domain credentials to install the driver.\n\n"
                    "Best regards,\nIT Service Desk"
                ),
                "final_resolution": (
                    "Hello Carlos,\n\nTo connect to the universal badge printing spooler, press Win + R and enter: "
                    "\\\\printcorp.internal.corp\\FollowMe-Color. Authenticate with your CORP domain credentials to install the driver.\n\n"
                    "Best regards,\nIT Service Desk"
                ),
                "created_at": now - timedelta(days=1),
            },
            # 10. Pending Approval - Software Request needing Admin Rights
            {
                "customer_name": "Rachel Green",
                "customer_email": "rachel.green@example.com",
                "subject": "Requesting local admin rights to install Wireshark for packet capture",
                "description": "I need Wireshark installed to troubleshoot our team's microservice latency. Windows installer prompts for admin PIN.",
                "category": "software",
                "priority": "medium",
                "status": "pending_approval",
                "classifier_confidence": 0.92,
                "resolver_confidence": 0.85,
                "review_status": "needs_human_approval",
                "draft_resolution": (
                    "Hello Rachel,\n\nWireshark is available in the Company Portal self-service catalog without requiring permanent admin rights. "
                    "If you require WinPcap/Npcap kernel driver elevation, request a 4-hour PAM elevation token at https://pam.internal.corp."
                ),
                "final_resolution": None,
                "created_at": now - timedelta(minutes=45),
            },
        ]

        for item in sample_tickets:
            created_at = item.pop("created_at")
            ticket = Ticket(**item)
            ticket.created_at = created_at
            ticket.updated_at = created_at
            db.add(ticket)
            db.flush()

            # Add agent log records
            log1 = AgentLog(
                ticket_id=ticket.id,
                agent_name="classifier",
                input_data=f'{{"subject": "{ticket.subject}", "category": "{ticket.category}"}}',
                output_data=f'{{"category": "{ticket.category}", "priority": "{ticket.priority}", "confidence": {ticket.classifier_confidence}}}',
                timestamp=created_at + timedelta(seconds=2),
            )
            log2 = AgentLog(
                ticket_id=ticket.id,
                agent_name="resolver",
                input_data=f'{{"ticket_id": {ticket.id}, "category": "{ticket.category}"}}',
                output_data=f'{{"confidence": {ticket.resolver_confidence}, "reasoning": "KB matched and draft formulated."}}',
                timestamp=created_at + timedelta(seconds=5),
            )
            log3 = AgentLog(
                ticket_id=ticket.id,
                agent_name="reviewer",
                input_data=f'{{"review_target": "draft_resolution", "priority": "{ticket.priority}"}}',
                output_data=f'{{"decision": "{ticket.review_status}", "confidence": 0.92}}',
                timestamp=created_at + timedelta(seconds=8),
            )
            db.add_all([log1, log2, log3])

            # Add approval record for pending approval tickets
            if ticket.status == "pending_approval":
                approval = Approval(
                    ticket_id=ticket.id,
                    status="pending",
                    reviewer_notes=f"Awaiting human approval due to {ticket.priority} priority or safety review policy.",
                    created_at=created_at + timedelta(seconds=9),
                )
                db.add(approval)

        db.commit()
        print(f"Successfully seeded {len(sample_tickets)} sample tickets with agent traces and approvals.")

    except Exception as exc:
        db.rollback()
        print(f"Error seeding database: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_tickets()
