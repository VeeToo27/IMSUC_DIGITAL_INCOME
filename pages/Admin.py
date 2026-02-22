import streamlit as st
import sys, os, re
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (COMMON_CSS, get_all_users, load_stalls, update_balance,
                   get_all_tokens, get_tokens_for_stall, top_bar,
                   block_user, unblock_user, esc, stat_card)

st.set_page_config(page_title="Vault — Admin", page_icon="🛠️", layout="centered", initial_sidebar_state="collapsed")
st.markdown(COMMON_CSS, unsafe_allow_html=True)

if st.session_state.get("role") != "admin":
    st.switch_page("app.py")

admin = st.session_state.current_admin
top_bar("Admin Panel", admin["username"], "ADMINISTRATOR", color="#b91c1c")

tab_dash, tab_users, tab_txn, tab_topup = st.tabs(["📊 Dashboard", "👥 Users", "📋 Transactions", "💰 Top Up"])

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    try:
        users  = get_all_users()
        stalls = load_stalls()
        tokens = get_all_tokens()

        total_bal     = sum(float(u.get("Amount",0) or 0) for u in users)
        total_revenue = sum(float(t.get("Total",0) or 0) for t in tokens)
        pending_all   = len([t for t in tokens if str(t.get("Status","")).strip() != "Served"])
        served_all    = len([t for t in tokens if str(t.get("Status","")).strip() == "Served"])

        c1, c2 = st.columns(2)
        with c1: stat_card(len(users),    "Users",        "#818cf8")
        with c2: stat_card(f"₹{total_bal:,.0f}", "In System", "#34d399")
        c1, c2 = st.columns(2)
        with c1: stat_card(len(tokens),   "Total Orders",  "#d97706")
        with c2: stat_card(f"₹{total_revenue:,.0f}", "Revenue", "#a78bfa")
        c1, c2 = st.columns(2)
        with c1: stat_card(pending_all,   "Pending",       "#f59e0b")
        with c2: stat_card(served_all,    "Served",        "#34d399")

        if stalls:
            st.markdown('<div class="section-title" style="margin-top:1rem;">🏪 Per-Stall</div>', unsafe_allow_html=True)
            for s in stalls:
                s_tok     = [t for t in tokens if str(t.get("Stall_ID","")).strip() == s["id"]]
                s_rev     = sum(float(t.get("Total",0) or 0) for t in s_tok)
                s_pending = len([t for t in s_tok if str(t.get("Status","")).strip() != "Served"])
                st.markdown(f"""
                <div class="card card-orange">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                      <div style="font-size:0.92rem;font-weight:800;color:#e2e8f0;">{esc(s['name'])}</div>
                      <div style="font-size:0.68rem;font-family:'Space Mono',monospace;color:#475569;">{esc(s['id'])}</div>
                    </div>
                    <div style="text-align:right;">
                      <div style="font-family:'Space Mono',monospace;font-size:0.92rem;font-weight:700;color:#34d399;">₹{s_rev:,.0f}</div>
                      <div style="font-size:0.68rem;color:#64748b;">{len(s_tok)} orders · {s_pending} pending</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

        st.markdown(f'<p class="hint">Last updated: {datetime.now().strftime("%d %b, %I:%M %p")}</p>', unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="ref_dash"): st.rerun()
    except FileNotFoundError: st.error("❌ Excel file not found.")
    except Exception as e:    st.error(f"Error: {esc(str(e))}")

# ══════════════════════════════════════════════════════════════════════════════
# USERS — list, block/unblock, zero balance
# ══════════════════════════════════════════════════════════════════════════════
with tab_users:
    try:
        users = get_all_users()
        if not users:
            st.info("No users registered yet.")
        else:
            search = st.text_input("Search", placeholder="Username or UID", key="usr_search")
            filtered = [u for u in users if not search.strip() or
                        search.strip().lower() in str(u.get("Username","")).lower() or
                        search.strip().lower() in str(u.get("UID","")).lower()]

            for u in filtered:
                uname      = str(u.get("Username",""))
                uid        = str(u.get("UID",""))
                is_blocked = str(u.get("Pin","")).upper() == "BLOCKED"
                try:    bal = float(u.get("Amount",0) or 0)
                except: bal = 0.0

                icon = "🔒" if is_blocked else "👤"
                with st.expander(f"{icon} {esc(uname)}  ·  {esc(uid)}"):
                    st.markdown(f"""
                    <div class="info-row">
                      <span class="info-label">UID</span>
                      <span class="info-value">{esc(uid)}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">Balance</span>
                      <span class="info-value">₹{bal:,.2f}</span>
                    </div>
                    <div class="info-row">
                      <span class="info-label">Status</span>
                      <span class="info-value">{'🔒 Blocked' if is_blocked else '✅ Active'}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        if not is_blocked:
                            if st.button(f"🔒 Block", key=f"blk_{uname}"):
                                if block_user(uname):
                                    st.success(f"✅ {esc(uname)} blocked.")
                                    st.rerun()
                        else:
                            np = st.text_input("New PIN", key=f"np_{uname}", max_chars=4, placeholder="4 digits")
                            if st.button(f"🔓 Unblock", key=f"ublk_{uname}"):
                                if re.match(r"^\d{4}$", np or ""):
                                    if unblock_user(uname, np):
                                        st.success(f"✅ {esc(uname)} unblocked.")
                                        st.rerun()
                                else:
                                    st.warning("Enter a valid 4-digit PIN.")
                    with c2:
                        if st.button("🔄 Zero Balance", key=f"zero_{uname}"):
                            if update_balance(uname, 0):
                                st.success(f"✅ Balance zeroed for {esc(uname)}.")
                                st.rerun()

        if st.button("🔄 Refresh", key="ref_usr"): st.rerun()
    except FileNotFoundError: st.error("❌ Excel file not found.")
    except Exception as e:    st.error(f"Error: {esc(str(e))}")

# ══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS — full history, filterable
# ══════════════════════════════════════════════════════════════════════════════
with tab_txn:
    try:
        all_tokens = get_all_tokens()
        if not all_tokens:
            st.info("No transactions yet.")
        else:
            cf1, cf2 = st.columns(2)
            with cf1:
                stall_ids    = sorted(set(str(t.get("Stall_ID","")) for t in all_tokens))
                stall_filter = st.selectbox("Stall", ["All"] + stall_ids, key="tf_stall")
            with cf2:
                status_filter = st.selectbox("Status", ["All","Pending","Served"], key="tf_status")
            user_q = st.text_input("Search username", placeholder="Username", key="tf_user")

            display = all_tokens
            if stall_filter  != "All":     display = [t for t in display if str(t.get("Stall_ID","")) == stall_filter]
            if status_filter != "All":     display = [t for t in display if str(t.get("Status","")).strip() == status_filter]
            if user_q.strip():             display = [t for t in display if user_q.strip().lower() in str(t.get("Username","")).lower()]

            frev = sum(float(t.get("Total",0) or 0) for t in display)
            st.markdown(f"""
            <div class="card" style="border-left-color:#a78bfa;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:0.72rem;font-weight:800;text-transform:uppercase;color:#64748b;">
                  {len(display)} transaction{'s' if len(display)!=1 else ''}
                </span>
                <span style="font-family:'Space Mono',monospace;font-weight:700;color:#a78bfa;">₹{frev:,.2f}</span>
              </div>
            </div>""", unsafe_allow_html=True)

            for t in reversed(display):
                status    = str(t.get("Status","Pending")).strip()
                is_served = status == "Served"
                badge     = '<span class="green-badge">✅ Served</span>' if is_served else '<span class="orange-badge">⏳ Pending</span>'
                border    = "#059669" if is_served else "#f59e0b"
                st.markdown(f"""
                <div class="card" style="border-left-color:{border};">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                      <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:1.25rem;font-weight:900;color:#818cf8;font-family:'Space Mono',monospace;">
                          #{esc(t.get('Token_No',''))}
                        </span>
                        <span style="font-size:0.78rem;font-weight:800;color:#d97706;">{esc(t.get('Stall_Name',''))}</span>
                      </div>
                      <div style="font-size:0.78rem;font-weight:700;color:#94a3b8;margin-top:3px;">
                        👤 {esc(t.get('Username',''))}
                      </div>
                      <div style="font-size:0.7rem;color:#64748b;margin-top:2px;">{esc(t.get('Items',''))}</div>
                      <div style="font-size:0.63rem;color:#475569;margin-top:2px;">🕐 {esc(t.get('Time',''))}</div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;margin-left:8px;">
                      {badge}
                      <div style="font-family:'Space Mono',monospace;font-size:0.9rem;
                           font-weight:700;color:#e2e8f0;margin-top:5px;">₹{esc(t.get('Total','0'))}</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

        if st.button("🔄 Refresh", key="ref_txn"): st.rerun()
    except FileNotFoundError: st.error("❌ Excel file not found.")
    except Exception as e:    st.error(f"Error: {esc(str(e))}")

# ══════════════════════════════════════════════════════════════════════════════
# TOP UP
# ══════════════════════════════════════════════════════════════════════════════
with tab_topup:
    try:
        users        = get_all_users()
        active_users = [u for u in users if str(u.get("Pin","")).upper() != "BLOCKED"]
        usernames    = [u.get("Username","") for u in active_users if u.get("Username")]
        if not usernames:
            st.info("No active users.")
        else:
            selected = st.selectbox("Select User", usernames, key="tu_sel")
            if selected:
                udata = next((u for u in active_users if u.get("Username","") == selected), None)
                try:    cur_bal = float(udata.get("Amount",0) or 0)
                except: cur_bal = 0.0

                st.markdown(f"""
                <div class="card">
                  <div style="font-size:0.68rem;font-weight:800;text-transform:uppercase;
                       letter-spacing:0.07em;color:#64748b;">Current Balance</div>
                  <div style="font-family:'Space Mono',monospace;font-size:1.4rem;
                       font-weight:700;color:#818cf8;margin-top:4px;">₹{cur_bal:,.2f}</div>
                </div>""", unsafe_allow_html=True)

                amount = st.number_input("Amount (₹)", min_value=1.0, max_value=100000.0, value=100.0, step=50.0)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("➕ Add"):
                        if update_balance(selected, cur_bal + amount):
                            st.success(f"✅ ₹{amount:.0f} added → {esc(selected)} now has ₹{cur_bal+amount:.2f}")
                            st.rerun()
                        else: st.error("❌ Failed.")
                with c2:
                    if st.button("🔄 Set"):
                        if update_balance(selected, amount):
                            st.success(f"✅ Balance set to ₹{amount:.0f} for {esc(selected)}")
                            st.rerun()
                        else: st.error("❌ Failed.")
    except FileNotFoundError: st.error("❌ Excel file not found.")
    except Exception as e:    st.error(f"Error: {esc(str(e))}")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔓 Sign Out"):
    for k in ["role","current_admin"]:
        st.session_state.pop(k, None)
    st.switch_page("app.py")
