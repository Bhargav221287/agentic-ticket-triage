"""Streamlit dashboard for Agentic Ticket Triage system.

Interacts with the FastAPI backend to display ticket queues, trigger multi-agent
workflows, audit agent reasoning traces, and execute human-in-the-loop approvals.
"""

import os
import json
from datetime import datetime
import requests
import streamlit as st

# Configuration
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8010").rstrip("/")

st.set_page_config(
    page_title="Agentic Ticket Triage | IT Service Desk",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #e9ecef;
    }
    .badge-critical { background-color: #ff4b4b; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-high { background-color: #ffa421; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-medium { background-color: #2196f3; color: white; padding: 3px 8px; border-radius: 4px; }
    .badge-low { background-color: #78909c; color: white; padding: 3px 8px; border-radius: 4px; }
    .badge-resolved { background-color: #2e7d32; color: white; padding: 3px 8px; border-radius: 4px; }
    .badge-pending { background-color: #f57c00; color: white; padding: 3px 8px; border-radius: 4px; }
    .agent-box {
        border-left: 4px solid #1976d2;
        background: #f0f4f8;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def fetch_tickets(status_filter=None, category_filter=None, priority_filter=None):
    """Fetch tickets from the FastAPI backend."""
    params = {}
    if status_filter and status_filter != "All":
        params["status"] = status_filter
    if category_filter and category_filter != "All":
        params["category"] = category_filter
    if priority_filter and priority_filter != "All":
        params["priority"] = priority_filter

    try:
        resp = requests.get(f"{BACKEND_URL}/tickets", params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"Failed to fetch tickets: {resp.text}")
        return []
    except requests.exceptions.RequestException as e:
        st.warning(f"Unable to connect to backend at {BACKEND_URL}: {e}")
        return []


def fetch_ticket_detail(ticket_id: int):
    """Fetch complete ticket details and full agent execution trace."""
    try:
        resp = requests.get(f"{BACKEND_URL}/tickets/{ticket_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"Error fetching ticket #{ticket_id}: {resp.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Backend connection error: {e}")
        return None


def submit_ticket_api(payload: dict):
    """Submit a new ticket and trigger LangGraph execution."""
    try:
        resp = requests.post(f"{BACKEND_URL}/tickets", json=payload, timeout=45)
        if resp.status_code in [200, 201]:
            return resp.json(), None
        return None, resp.text
    except requests.exceptions.RequestException as e:
        return None, str(e)


def approve_ticket_api(ticket_id: int, edited_response: str = None, notes: str = None):
    """Approve a pending ticket."""
    payload = {}
    if edited_response:
        payload["edited_response"] = edited_response
    if notes:
        payload["reviewer_notes"] = notes
    try:
        resp = requests.post(f"{BACKEND_URL}/tickets/{ticket_id}/approve", json=payload, timeout=15)
        if resp.status_code == 200:
            return resp.json(), None
        return None, resp.text
    except requests.exceptions.RequestException as e:
        return None, str(e)


def reject_ticket_api(ticket_id: int, notes: str = None):
    """Reject a pending ticket."""
    payload = {}
    if notes:
        payload["reviewer_notes"] = notes
    try:
        resp = requests.post(f"{BACKEND_URL}/tickets/{ticket_id}/reject", json=payload, timeout=15)
        if resp.status_code == 200:
            return resp.json(), None
        return None, resp.text
    except requests.exceptions.RequestException as e:
        return None, str(e)


# Header & System Metrics
st.title("🛡️ Agentic IT Support Ticket Triage")
st.caption("Powered by LangGraph Multi-Agent Orchestration • FastAPI • SQLite • Human-in-the-Loop Safeguards")

all_tickets = fetch_tickets()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Tickets", len(all_tickets))
with col2:
    resolved_count = sum(1 for t in all_tickets if t.get("status") == "resolved")
    st.metric("Auto-Resolved / Closed", resolved_count)
with col3:
    pending_count = sum(1 for t in all_tickets if t.get("status") == "pending_approval")
    st.metric("Awaiting Human Approval", pending_count, delta="HITL Action Needed" if pending_count > 0 else "Clear")
with col4:
    confidences = [t.get("classifier_confidence") for t in all_tickets if t.get("classifier_confidence") is not None]
    avg_conf = (sum(confidences) / len(confidences) * 100) if confidences else 0.0
    st.metric("Avg Classifier Confidence", f"{avg_conf:.1f}%")

st.divider()

# Navigation Tabs
tab_queue, tab_approvals, tab_submit, tab_trace = st.tabs([
    "📋 Ticket Queue",
    "⚖️ Human Approval Queue",
    "➕ Submit New Ticket",
    "🔍 Deep Agent Trace & Audit",
])

# TAB 1: TICKET QUEUE
with tab_queue:
    st.subheader("Support Ticket Queue")
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 1])
    with f_col1:
        stat_filter = st.selectbox("Status", ["All", "pending_approval", "resolved", "open", "rejected"], key="q_stat")
    with f_col2:
        cat_filter = st.selectbox("Category", ["All", "network", "access", "hardware", "software", "other"], key="q_cat")
    with f_col3:
        prio_filter = st.selectbox("Priority", ["All", "critical", "high", "medium", "low"], key="q_prio")
    with f_col4:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    filtered_tickets = fetch_tickets(stat_filter, cat_filter, prio_filter)

    if not filtered_tickets:
        st.info("No tickets match the selected filters.")
    else:
        for t in filtered_tickets:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1, 4, 2, 2, 2])
                with c1:
                    st.write(f"**#{t['id']}**")
                with c2:
                    st.write(f"**{t['subject']}**")
                    st.caption(f"From: {t['customer_name']} ({t['customer_email']})")
                with c3:
                    cat = t.get("category") or "Unclassified"
                    prio = t.get("priority") or "medium"
                    st.write(f"**Category:** {cat}")
                    st.write(f"**Priority:** {prio.upper()}")
                with c4:
                    status_val = t.get("status", "open")
                    if status_val == "resolved":
                        st.markdown('<span class="badge-resolved">Resolved</span>', unsafe_allow_html=True)
                    elif status_val == "pending_approval":
                        st.markdown('<span class="badge-pending">Pending Approval</span>', unsafe_allow_html=True)
                    else:
                        st.write(f"`{status_val}`")

                    conf = t.get("classifier_confidence")
                    if conf is not None:
                        st.caption(f"Conf: {conf * 100:.0f}%")
                with c5:
                    if st.button("Inspect Trace", key=f"btn_trace_{t['id']}"):
                        st.session_state["selected_ticket_id"] = t["id"]
                        st.rerun()
                st.divider()

# TAB 2: PENDING HUMAN APPROVALS
with tab_approvals:
    st.subheader("⚖️ Human-in-the-Loop Review & Authorization")
    st.info(
        "Tickets appear here when priority is Critical, agent confidence is below 70%, "
        "or potential policy/security violations were flagged. A human supervisor must verify the resolution."
    )

    pending_tickets = [t for t in all_tickets if t.get("status") == "pending_approval"]

    if not pending_tickets:
        st.success("🎉 No tickets currently pending human authorization. All queues are clear!")
    else:
        for pt in pending_tickets:
            detail = fetch_ticket_detail(pt["id"])
            if not detail:
                continue

            with st.expander(f"⚠️ Ticket #{detail['id']}: {detail['subject']} ({detail.get('priority', '').upper()})", expanded=True):
                p_col1, p_col2 = st.columns([1, 1])
                with p_col1:
                    st.write(f"**Customer:** {detail['customer_name']} ({detail['customer_email']})")
                    st.write(f"**Category:** `{detail.get('category')}` | **Priority:** `{detail.get('priority')}`")
                    st.write(f"**Classifier Confidence:** `{detail.get('classifier_confidence', 0) * 100:.1f}%`")
                    st.write(f"**Resolver Confidence:** `{detail.get('resolver_confidence', 0) * 100:.1f}%`")
                    st.text_area("Customer Description", detail["description"], height=100, disabled=True, key=f"desc_{detail['id']}")

                with p_col2:
                    st.markdown("**Proposed Draft Resolution (Agent Draft):**")
                    draft_text = detail.get("draft_resolution") or "No draft generated."
                    edited_res = st.text_area(
                        "Edit Resolution Before Sending (Optional)",
                        value=draft_text,
                        height=140,
                        key=f"edit_res_{detail['id']}",
                    )
                    supervisor_notes = st.text_input(
                        "Supervisor Audit Notes",
                        placeholder="e.g. Verified employee identity; resolution validated.",
                        key=f"notes_{detail['id']}",
                    )

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("✅ Approve & Send", key=f"appr_{detail['id']}", type="primary", use_container_width=True):
                            with st.spinner("Authorizing and sending resolution..."):
                                _, err = approve_ticket_api(detail["id"], edited_response=edited_res, notes=supervisor_notes)
                                if err:
                                    st.error(f"Approval failed: {err}")
                                else:
                                    st.success(f"Ticket #{detail['id']} approved and resolved successfully!")
                                    st.rerun()
                    with btn_c2:
                        if st.button("❌ Reject Draft", key=f"rej_{detail['id']}", use_container_width=True):
                            with st.spinner("Rejecting draft..."):
                                _, err = reject_ticket_api(detail["id"], notes=supervisor_notes)
                                if err:
                                    st.error(f"Rejection failed: {err}")
                                else:
                                    st.warning(f"Ticket #{detail['id']} rejected.")
                                    st.rerun()

# TAB 3: SUBMIT NEW TICKET
with tab_submit:
    st.subheader("➕ Submit a Support Ticket")
    st.caption("Submitting initiates the LangGraph triage agents: Classifier ➔ Resolver ➔ Reviewer ➔ Conditional Routing.")

    with st.form("new_ticket_form", clear_on_submit=False):
        f_name = st.text_input("Customer Name", value="Alex Rivera")
        f_email = st.text_input("Customer Email", value="alex.rivera@example.com")
        f_subject = st.text_input("Ticket Subject", value="Unable to connect to GlobalProtect VPN after system update")
        f_description = st.text_area(
            "Issue Description",
            value="Since updating macOS this morning, GlobalProtect gets stuck on 'Connecting to gateway'. "
                  "I already restarted my laptop. I cannot access the internal database.",
            height=120,
        )

        submit_btn = st.form_submit_button("🚀 Submit Ticket & Run Agent Workflow", type="primary")

    if submit_btn:
        if not f_name or not f_email or not f_subject or not f_description:
            st.error("Please fill in all ticket fields.")
        else:
            payload = {
                "customer_name": f_name,
                "customer_email": f_email,
                "subject": f_subject,
                "description": f_description,
            }
            with st.spinner("Running LangGraph multi-agent workflow (Classifier ➔ Resolver ➔ Reviewer)..."):
                result, err = submit_ticket_api(payload)
                if err:
                    st.error(f"Workflow execution failed: {err}")
                else:
                    st.success(f"Ticket #{result['id']} processed! Status: **{result['status'].upper()}**")
                    st.session_state["selected_ticket_id"] = result["id"]

                    # Quick summary cards
                    q1, q2, q3 = st.columns(3)
                    with q1:
                        st.info(f"**Classification:** {result.get('category')} (Priority: {result.get('priority')})")
                    with q2:
                        st.info(f"**Confidence:** {result.get('classifier_confidence', 0)*100:.0f}%")
                    with q3:
                        st.info(f"**Review Outcome:** {result.get('review_status')}")

# TAB 4: DEEP AGENT TRACE & AUDIT
with tab_trace:
    st.subheader("🔍 Deep Agent Trace & Audit Log")
    st.caption("Inspect the exact reasoning, tool lookups, and decision points for every agent in the pipeline.")

    ticket_ids = [t["id"] for t in all_tickets]
    default_index = 0
    selected_id = st.session_state.get("selected_ticket_id")
    if selected_id and selected_id in ticket_ids:
        default_index = ticket_ids.index(selected_id)

    chosen_ticket_id = st.selectbox("Select Ticket to Inspect", ticket_ids, index=default_index if ticket_ids else 0)

    if chosen_ticket_id:
        t_data = fetch_ticket_detail(chosen_ticket_id)
        if t_data:
            st.markdown(f"### Ticket #{t_data['id']}: {t_data['subject']}")
            st.write(f"**Customer:** {t_data['customer_name']} ({t_data['customer_email']}) | **Created:** {t_data['created_at']}")
            st.write(f"**Status:** `{t_data['status']}` | **Category:** `{t_data['category']}` | **Priority:** `{t_data['priority']}`")

            st.markdown("#### 1. Classifier Agent")
            st.markdown(
                f"""
                <div class="agent-box">
                    <strong>Assigned Category:</strong> <code>{t_data.get('category')}</code><br>
                    <strong>Assigned Priority:</strong> <code>{t_data.get('priority')}</code><br>
                    <strong>Confidence:</strong> <code>{t_data.get('classifier_confidence', 0)*100:.1f}%</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### 2. Resolver Agent")
            draft = t_data.get("draft_resolution") or "No draft generated."
            st.markdown(
                f"""
                <div class="agent-box">
                    <strong>Drafted Resolution:</strong><br>
                    <pre style="white-space: pre-wrap; font-family: inherit;">{draft}</pre>
                    <strong>Resolver Confidence:</strong> <code>{t_data.get('resolver_confidence', 0)*100:.1f}%</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### 3. Reviewer Agent & Policy Verification")
            rev_status = t_data.get("review_status")
            st.markdown(
                f"""
                <div class="agent-box">
                    <strong>Review Decision:</strong> <code>{rev_status}</code><br>
                    <strong>Final Ticket Status:</strong> <code>{t_data.get('status')}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if t_data.get("final_resolution"):
                st.markdown("#### ✅ Dispatched Final Resolution")
                st.success(t_data["final_resolution"])

            # Raw Agent Logs Table
            st.markdown("#### Detailed Execution Log Entries")
            logs = t_data.get("agent_logs", [])
            if logs:
                for idx, log in enumerate(logs):
                    with st.expander(f"Step {idx + 1}: {log['agent_name'].upper()} at {log['timestamp']}"):
                        st.markdown("**Input Data:**")
                        try:
                            st.json(json.loads(log["input_data"]))
                        except Exception:
                            st.text(log["input_data"])

                        st.markdown("**Output Data:**")
                        try:
                            st.json(json.loads(log["output_data"]))
                        except Exception:
                            st.text(log["output_data"])
            else:
                st.write("No granular logs recorded for this ticket.")
