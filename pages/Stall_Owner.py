import streamlit as st
import sys, os, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import COMMON_CSS, get_tokens_for_stall, mark_token_served, top_bar, esc, stat_card

st.set_page_config(page_title="Vault — Stall Owner", page_icon="🧑‍🍳", layout="centered", initial_sidebar_state="collapsed")
st.markdown(COMMON_CSS, unsafe_allow_html=True)

if st.session_state.get("role") != "stall_owner":
    st.switch_page("app.py")

stall = st.session_state.current_stall
top_bar("Stall Owner", stall["name"], stall["id"], color="#b45309")

tab_orders, tab_menu = st.tabs(["🎟️ Orders", "🍽️ Menu"])

# ══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_orders:
    tokens  = get_tokens_for_stall(stall["id"])
    pending = [t for t in tokens if str(t.get("Status","")).strip() != "Served"]
    served  = [t for t in tokens if str(t.get("Status","")).strip() == "Served"]

    c1, c2, c3 = st.columns(3)
    with c1: stat_card(len(tokens), "Total",   "#d97706")
    with c2: stat_card(len(pending), "Pending", "#f59e0b")
    with c3: stat_card(len(served),  "Served",  "#34d399")

    now_str = datetime.now().strftime("%I:%M:%S %p")
    st.markdown(f'<p class="hint">🔄 Updated {now_str} · auto-refreshes every 10s</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    show = st.radio("Show", ["⏳ Pending", "✅ Served", "All"], horizontal=True, key="show_filter")
    if show == "⏳ Pending":  display = pending
    elif show == "✅ Served": display = served
    else:                     display = tokens

    if not display:
        st.info("No orders here yet." if not tokens else "No orders in this filter.")
    else:
        for t in reversed(display):
            status    = str(t.get("Status","Pending")).strip()
            is_served = status == "Served"
            token_no  = t.get("Token_No","")
            badge     = '<span class="green-badge">✅ Served</span>' if is_served else '<span class="orange-badge">⏳ Pending</span>'
            border    = "#059669" if is_served else "#f59e0b"

            ci, cb = st.columns([4, 1.4])
            with ci:
                st.markdown(f"""
                <div class="card" style="border-left-color:{border};">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                      <div style="font-size:1.5rem;font-weight:900;color:#818cf8;
                           font-family:'Space Mono',monospace;line-height:1.1;">
                        #{esc(token_no)}
                      </div>
                      <div style="font-size:0.8rem;font-weight:800;color:#94a3b8;margin-top:4px;">
                        👤 {esc(t.get('Username',''))}
                      </div>
                      <div style="font-size:0.73rem;color:#64748b;margin-top:3px;">
                        {esc(t.get('Items',''))}
                      </div>
                      <div style="font-size:0.65rem;color:#475569;margin-top:3px;">
                        🕐 {esc(t.get('Time',''))}
                      </div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;margin-left:8px;">
                      {badge}
                      <div style="font-family:'Space Mono',monospace;font-size:0.88rem;
                           font-weight:700;color:#e2e8f0;margin-top:5px;">
                        ₹{esc(t.get('Total','0'))}
                      </div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with cb:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                lbl = "✅ Served" if not is_served else "↩️ Undo"
                if st.button(lbl, key=f"srv_{token_no}_{stall['id']}"):
                    if mark_token_served(token_no, stall["id"]):
                        st.rerun()

    time.sleep(10)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════════════════════
with tab_menu:
    st.markdown('<div class="section-title">🍽️ Your Menu</div>', unsafe_allow_html=True)
    if not stall["menu"]:
        st.info("No menu items found.")
    else:
        for item in stall["menu"]:
            st.markdown(f"""
            <div class="card card-orange">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:0.92rem;font-weight:800;color:#e2e8f0;">{esc(item['item'])}</div>
                <div style="font-family:'Space Mono',monospace;font-size:0.95rem;font-weight:700;color:#d97706;">
                  ₹{item['price']:.0f}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-row"><span class="info-label">Stall ID</span>
      <span class="info-value">{esc(stall['id'])}</span></div>
    <div class="info-row"><span class="info-label">Menu Items</span>
      <span class="info-value">{len(stall['menu'])}</span></div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔓 Sign Out"):
    for k in ["role", "current_stall"]:
        st.session_state.pop(k, None)
    st.switch_page("app.py")
